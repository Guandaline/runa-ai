"""
Abstract Base Class for LLM Providers.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

from nala.athomic.ai.governance.guards.protocol import (
    AIGuardInputProtocol,
    AIGuardOutputProtocol,
)
from nala.athomic.ai.governance.pipeline import GuardPipeline
from nala.athomic.ai.llm.protocol import LLMProviderProtocol
from nala.athomic.ai.schemas.llms import LLMResponse, LLMResponseChunk
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.config.schemas.ai.llm.llm_settings import LLMConnectionSettings
from nala.athomic.observability.metrics.enums import MetricStatus
from nala.athomic.observability.metrics.usage.ai.llm_metrics import (
    llm_operation_duration_seconds,
    llm_operations_total,
    llm_token_usage_total,
)
from nala.athomic.observability.tracing import SpanKind, StatusCode
from nala.athomic.observability.tracing.attributes import (
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_SYSTEM,
)
from nala.athomic.services.base import BaseService

S = TypeVar("S", bound=BaseModel)
T = TypeVar("T", bound=BaseModel)


class BaseLLM(BaseService, LLMProviderProtocol, Generic[S], ABC):
    """
    Abstract base class for all LLM providers (Vertex, OpenAI, etc.).

    This class implements the Template Method pattern to enforce:
    1. Lifecycle Management (Startup/Shutdown via BaseService).
    2. Unified Observability (Tracing, Metrics, Logging).
    3. Error Handling boundaries.

    Note: Governance (Guards) is handled by the LLMManager/GuardPipeline
    before calling this provider.
    """

    def __init__(
        self,
        connection_settings: LLMConnectionSettings,
    ) -> None:
        self.connection_settings: LLMConnectionSettings = connection_settings
        self.settings: S = connection_settings.provider  # type: ignore

        service_name = (
            f"llm_{connection_settings.backend}_{connection_settings.default_model}"
        )

        super().__init__(
            service_name=service_name,
            enabled=connection_settings.enabled,
        )

        self.default_model = connection_settings.default_model

        # Injected by LLMManager
        self.guards: List[AIGuardInputProtocol] = []
        self.output_guards: List[AIGuardOutputProtocol] = []

    def get_output_max_tokens(self) -> int:
        """
        Helper to get max output tokens from generation settings.
        """
        return self.connection_settings.generation.max_output_tokens

    async def generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Public method for generation (Text or Tool Calls) with observability.
        """
        operation = "generate"
        start_time = time.perf_counter()
        status = MetricStatus.FAILURE

        if not self.is_ready():
            await self.wait_ready()

        # 1. Input Governance Check (Blocking)
        if self.guards:
            await GuardPipeline(input_guards=self.guards).validate_input(
                prompt=prompt or "", **kwargs
            )

        with self.tracer.start_as_current_span(
            f"llm.{operation}", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute(LLM_SYSTEM, self.service_name)
            span.set_attribute(LLM_MODEL, self.default_model)
            span.set_attribute(LLM_PROVIDER, self.connection_settings.backend)
            if tools:
                span.set_attribute("llm.tools_count", len(tools))

            try:
                self.logger.debug(f"Generating content with model {self.default_model}")

                timeout = kwargs.get("timeout", self.connection_settings.timeout)

                # Call concrete implementation
                result: LLMResponse = await self._generate(
                    prompt,
                    system_message,
                    tools=tools,
                    timeout=timeout,
                    **kwargs,
                )

                # 2. Output Governance Check (Non-Blocking, Can Modify Response)
                if self.output_guards:
                    result = await GuardPipeline(
                        output_guards=self.output_guards
                    ).process_output(result, **kwargs)

                if result.usage:
                    self.record_token_usage(
                        prompt_tokens=result.usage.prompt_tokens,
                        completion_tokens=result.usage.completion_tokens,
                    )

                status = MetricStatus.SUCCESS
                span.set_status(StatusCode.OK)
                return result

            except Exception as e:
                self.logger.error("LLM generation failed: {}", e, exc_info=True)
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise

            finally:
                duration = time.perf_counter() - start_time

                llm_operation_duration_seconds.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                ).observe(duration)

                llm_operations_total.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                    status=status,
                ).inc()

    async def stream_content(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Public method for streamed generation (Text or Tool Calls) with observability.
        The LLM's response is yielded incrementally.
        """
        operation = "stream_content"
        start_time = time.perf_counter()
        status = MetricStatus.FAILURE
        total_content_length = 0

        if not self.is_ready():
            await self.wait_ready()

        # 1. Input Governance Check (Blocking)
        if self.guards:
            await GuardPipeline(input_guards=self.guards).validate_input(
                prompt=prompt or "", **kwargs
            )

        with self.tracer.start_as_current_span(
            f"llm.{operation}", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute(LLM_SYSTEM, self.service_name)
            span.set_attribute(LLM_MODEL, self.default_model)
            span.set_attribute(LLM_PROVIDER, self.connection_settings.backend)

            try:
                timeout = kwargs.get("timeout", self.connection_settings.timeout)

                # Call concrete implementation (stream)
                stream = self._stream_generate(
                    prompt,
                    system_message,
                    tools=tools,
                    timeout=timeout,
                    **kwargs,
                )

                async for chunk in stream:
                    # 2. Apply Output Governance (e.g., PII Sanitization) per chunk
                    if self.output_guards and chunk.content_delta:
                        # NOTE: Output Guards are designed to take an LLMResponse object,
                        # so this requires a wrapper for chunk-based processing,
                        # or accepting latency of blocking the stream briefly for batch sanitization.
                        # For now, we yield the raw delta, placing the responsibility on RAGService.
                        pass

                    total_content_length += len(chunk.content_delta or "")
                    yield chunk

                status = MetricStatus.SUCCESS
                span.set_attribute("llm.response_length", total_content_length)
                span.set_status(StatusCode.OK)

            except Exception as e:
                self.logger.error("LLM streaming failed: {}", e, exc_info=True)
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise

            finally:
                duration = time.perf_counter() - start_time

                llm_operation_duration_seconds.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                ).observe(duration)

                llm_operations_total.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                    status=status,
                ).inc()

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Public method for structured generation with observability.
        """
        operation = "generate_structured"
        start_time = time.perf_counter()
        status = MetricStatus.FAILURE

        if not self.is_ready():
            await self.wait_ready()

        # 1. Input Governance Check (Blocking)
        if self.guards:
            await GuardPipeline(input_guards=self.guards).validate_input(
                prompt=prompt or "", **kwargs
            )

        with self.tracer.start_as_current_span(
            f"llm.{operation}", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute(LLM_SYSTEM, self.service_name)
            span.set_attribute(LLM_MODEL, self.default_model)
            span.set_attribute(LLM_PROVIDER, self.connection_settings.backend)
            span.set_attribute("llm.schema", response_model.__name__)

            try:
                self.logger.debug(
                    f"Generating structured content ({response_model.__name__}) with {self.default_model}"
                )

                retries = max_retries or self.connection_settings.max_retries
                timeout = kwargs.get("timeout", self.connection_settings.timeout)

                result = await self._generate_structured(
                    prompt,
                    response_model,
                    system_message,
                    max_retries=retries,
                    timeout=timeout,
                    **kwargs,
                )

                status = MetricStatus.SUCCESS
                span.set_status(StatusCode.OK)
                return result

            except Exception as e:
                self.logger.error(
                    "LLM structured generation failed: {}", e, exc_info=True
                )
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise

            finally:
                duration = time.perf_counter() - start_time

                llm_operation_duration_seconds.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                ).observe(duration)

                llm_operations_total.labels(
                    provider=self.connection_settings.backend,
                    model=self.default_model,
                    operation=operation,
                    status=status,
                ).inc()

    def record_token_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """
        Helper method to record token usage metrics to Prometheus.
        """
        if prompt_tokens > 0:
            llm_token_usage_total.labels(
                provider=self.connection_settings.backend,
                model=self.default_model,
                token_type="prompt_tokens",
            ).inc(prompt_tokens)

        if completion_tokens > 0:
            llm_token_usage_total.labels(
                provider=self.connection_settings.backend,
                model=self.default_model,
                token_type="completion_tokens",
            ).inc(completion_tokens)

    @abstractmethod
    async def _generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Concrete implementations must override this to call the provider API.
        Must handle tool conversion and response normalization.
        """
        raise NotImplementedError

    @abstractmethod
    async def _stream_generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Concrete implementations must override this to stream the provider API response.
        """
        raise NotImplementedError

    @abstractmethod
    async def _generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Concrete implementations must override this to call the provider API for structured output.
        """
        raise NotImplementedError

    async def _connect(self) -> None:
        """
        Default implementation. API-based providers usually just set ready.
        """
        await self.set_ready()

    async def _close(self) -> None:
        """
        Default cleanup implementation.
        """
        pass
