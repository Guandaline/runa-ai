# src/nala/athomic/ai/llm/providers/openai_provider.py
"""
OpenAI implementation of the LLM Protocol with Tool Support.

This module provides the adapter for the OpenAI Chat Completion API, compatible with:
- Official OpenAI API
- Azure OpenAI Service
- Ollama (via OpenAI compatibility)
- vLLM and other compatible inference servers
"""

import json
from typing import Any, AsyncIterator, List, Optional, Type, TypeVar, Union

import instructor
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.llm.exceptions import (
    AuthenticationError,
    ContextWindowExceededError,
    InvalidRequestError,
    ProviderError,
    ProviderInitializationError,
    RateLimitError,
    StructuredOutputError,
)
from nala.athomic.ai.schemas import ToolCall
from nala.athomic.ai.schemas.llms import LLMResponse, LLMResponseChunk, TokenUsage
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.config.schemas.ai.llm import (
    AzureOpenAIProviderSettings,
    LLMConnectionSettings,
    OllamaProviderSettings,
    OpenAIProviderSettings,
)

T = TypeVar("T", bound=BaseModel)

ProviderSettingsType = Union[
    OpenAIProviderSettings, OllamaProviderSettings, AzureOpenAIProviderSettings
]
SettingsType = Union[LLMConnectionSettings, ProviderSettingsType]

CLIENT_NOT_CONNECTED_ERROR = "Client not connected"


class OpenAIProvider(BaseLLM[SettingsType]):
    """
    Adapter for OpenAI API and compatible interfaces.

    Wraps the AsyncOpenAI client, handles exception mapping, and implements
    the Athomic Tool Adapter pattern. It leverages centralized configuration
    for generation parameters (temperature, max_tokens) to ensure consistency.

    Key Features:
    - Polymorphic connection handling (OpenAI/Azure/Ollama).
    - Function Calling (Tool use) support.
    - Structured Output via `instructor`.
    - Automated metrics recording.
    """

    def __init__(self, connection_settings: SettingsType) -> None:
        """
        Initializes the OpenAI Provider.

        Args:
            connection_settings: The configuration object. Can be either the full
                                 LLMConnectionSettings or just the specific ProviderSettings.
        """
        super().__init__(connection_settings)
        self._client: Optional[AsyncOpenAI] = None

    async def _connect(self) -> None:
        """
        Initializes the OpenAI client using settings polymorphism.

        This method retrieves the specific connection parameters (like api_key,
        base_url, organization) from the settings object, which knows how to
        format them for the specific backend (e.g., appending /v1 for Ollama).
        """
        try:
            if hasattr(self.settings, "provider"):
                provider_config = self.settings.provider
            else:
                provider_config = self.settings

            client_params = provider_config.get_client_params()

            timeout = getattr(self.connection_settings, "timeout", 60.0)

            client_params["timeout"] = timeout
            client_params["max_retries"] = 0

            self._client = AsyncOpenAI(**client_params)

        except AttributeError as e:
            config_type = type(self.settings).__name__
            raise ProviderInitializationError(
                self.service_name,
                f"Configuration object {config_type} missing 'get_client_params' "
                f"implementation or 'provider' attribute. Error: {e}",
            ) from e
        except Exception as e:
            raise ProviderInitializationError(
                self.service_name, f"Failed to initialize OpenAI client: {e}"
            ) from e

    async def _close(self) -> None:
        """Closes the underlying HTTP client session."""
        if self._client:
            await self._client.close()

    def _convert_tools(self, tools: List[AIToolProtocol]) -> Optional[List[dict]]:
        """
        Adapter: Converts Athomic AITools into the OpenAI Tool format.

        Args:
            tools: List of Athomic tool implementations.

        Returns:
            List of dictionaries matching OpenAI's 'tools' schema.
        """
        if not tools:
            return None

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.schema,
                },
            }
            for tool in tools
        ]

    def _parse_response(self, response: Any) -> LLMResponse:
        """
        Adapter: Converts an OpenAI ChatCompletion object into a Athomic LLMResponse.

        Args:
            response: The raw response object from OpenAI SDK.

        Returns:
            Normalized LLMResponse.
        """
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    self.logger.warning(
                        f"Failed to parse arguments for tool {tc.function.name}"
                    )
                    args = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        usage = TokenUsage()
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage,
            model=response.model,
        )

    async def _generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generates text or tool calls using the OpenAI API.

        This method handles both simple prompts and full message history (via kwargs['messages']).
        It applies default generation settings (temperature, tokens) from the configuration
        unless explicitly overridden by kwargs.

        Args:
            prompt: The user input text (used if 'messages' is not in kwargs).
            system_message: Optional system instruction (used if 'messages' is not in kwargs).
            tools: List of tools available to the model.
            **kwargs: Additional generation parameters. Can include:
                      - messages: List[Dict] for full chat history.
                      - model: String to override the default model.
                      - temperature, max_tokens, etc.

        Returns:
            A normalized LLMResponse containing the model's output.

        Raises:
            ProviderInitializationError: If the OpenAI client is not properly connected.
            ProviderError: If the API call fails or returns an error.
            ValueError: If neither 'prompt' nor 'messages' is provided.
        """
        if not self._client:
            raise ProviderInitializationError(
                self.service_name, CLIENT_NOT_CONNECTED_ERROR
            )

        if "messages" in kwargs:
            messages = kwargs.pop("messages")
        else:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if prompt:
                messages.append({"role": "user", "content": prompt})

        if not messages:
            raise ValueError("Neither 'prompt' nor 'messages' provided for generation.")

        model_to_use = kwargs.pop("model", self.default_model)

        openai_tools = self._convert_tools(tools)

        gen_defaults = getattr(self.connection_settings, "generation", None)

        default_temp = gen_defaults.temperature if gen_defaults else 0.7
        default_max_tokens = gen_defaults.max_output_tokens if gen_defaults else 1024
        default_top_p = gen_defaults.top_p if gen_defaults else 1.0
        default_stop = gen_defaults.stop_sequences if gen_defaults else None

        # Build request parameters map
        request_kwargs = {
            "temperature": kwargs.get("temperature", default_temp),
            "max_tokens": kwargs.get("max_tokens", default_max_tokens),
            "top_p": kwargs.get("top_p", default_top_p),
            "stop": kwargs.get("stop", default_stop),
        }

        request_kwargs.update(
            {k: v for k, v in kwargs.items() if k not in request_kwargs}
        )

        try:
            response = await self._client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                **request_kwargs,
            )

            return self._parse_response(response)

        except openai.APIError as e:
            self._handle_openai_error(e)
            raise ProviderError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error in OpenAI provider: {e}") from e

    def _prepare_stream_request_params(self, kwargs: dict) -> dict:
        """
        Prepares request parameters for streaming by applying defaults.

        Args:
            kwargs: Raw keyword arguments from the caller.

        Returns:
            Dictionary with normalized request parameters.
        """
        gen_defaults = getattr(self.connection_settings, "generation", None)

        default_temp = kwargs.get(
            "temperature", gen_defaults.temperature if gen_defaults else 0.7
        )
        default_max_tokens = kwargs.get(
            "max_tokens", gen_defaults.max_output_tokens if gen_defaults else 1024
        )
        default_top_p = kwargs.get("top_p", gen_defaults.top_p if gen_defaults else 1.0)
        default_stop = kwargs.get(
            "stop", gen_defaults.stop_sequences if gen_defaults else None
        )

        request_kwargs = {
            "temperature": default_temp,
            "max_tokens": default_max_tokens,
            "top_p": default_top_p,
            "stop": default_stop,
        }
        request_kwargs.update(
            {k: v for k, v in kwargs.items() if k not in request_kwargs}
        )
        return request_kwargs

    def _process_stream_chunk(
        self, chunk: Any, model: str
    ) -> Optional[LLMResponseChunk]:
        """
        Processes a single stream chunk from OpenAI response.

        Args:
            chunk: Raw chunk from OpenAI streaming response.
            model: Model name for the response chunk.

        Returns:
            LLMResponseChunk if there's content to yield, None otherwise.
        """
        content_delta = chunk.choices[0].delta.content or None
        finish_reason = chunk.choices[0].finish_reason or None
        usage_model = None

        if chunk.usage:
            usage_model = TokenUsage(
                prompt_tokens=chunk.usage.prompt_tokens,
                completion_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens,
            )

        # Only create chunk if there's meaningful data
        if content_delta or finish_reason or usage_model:
            return LLMResponseChunk(
                content_delta=content_delta,
                finish_reason=finish_reason,
                usage=usage_model,
                model=model,
            )
        return None

    async def _stream_generate(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[AIToolProtocol]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Streams the LLM response chunks using the OpenAI API.

        This method generates content incrementally, yielding a chunk for each received delta.

        Args:
            prompt: The user input text.
            system_message: Optional system instruction.
            tools: List of tools available to the model.
            **kwargs: Additional generation parameters.

        Yields:
            LLMResponseChunk: Incremental response objects.

        Raises:
            ProviderInitializationError: If the OpenAI client is not connected.
            ProviderError: If the API call fails or returns an error.
        """
        if not self._client:
            raise ProviderInitializationError(
                self.service_name, CLIENT_NOT_CONNECTED_ERROR
            )

        # Prepare messages and parameters
        if "messages" in kwargs:
            messages = kwargs.pop("messages")
        else:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if prompt:
                messages.append({"role": "user", "content": prompt})

        model_to_use = kwargs.pop("model", self.default_model)
        openai_tools = self._convert_tools(tools)
        request_kwargs = self._prepare_stream_request_params(kwargs)

        # Start the streaming API call
        try:
            stream = await self._client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                stream=True,
                **request_kwargs,
            )

            # Process the stream
            async for chunk in stream:
                processed_chunk = self._process_stream_chunk(chunk, model_to_use)
                if processed_chunk:
                    yield processed_chunk

        except openai.APIError as e:
            self._handle_openai_error(e)
            raise ProviderError(f"OpenAI streaming error: {e}") from e
        except Exception as e:
            raise ProviderError(
                f"Unexpected error in OpenAI streaming provider: {e}"
            ) from e

    async def _generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Generates structured data conforming to a Pydantic model using 'instructor'.

        This leverages the `instructor` library to patch the OpenAI client, ensuring
        robust schema validation and automatic retries for JSON parsing.

        Args:
            prompt: The user prompt.
            response_model: The Pydantic model class defining the expected structure.
            system_message: Optional system instruction.
            max_retries: Number of retries for schema validation failures.
            **kwargs: Additional generation parameters.

        Returns:
            An instance of `response_model`.

        Raises:
            StructuredOutputError: If the model fails to produce valid JSON matching the schema.
            ProviderError: If the API call fails.
        """
        if not self._client:
            raise ProviderInitializationError(
                self.service_name, CLIENT_NOT_CONNECTED_ERROR
            )

        # Patch client for structured output
        instructor_client = instructor.from_openai(
            self._client,
            mode=instructor.Mode.TOOLS,
        )

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Safely access generation settings
        gen_defaults = getattr(self.connection_settings, "generation", None)
        default_temp = gen_defaults.temperature if gen_defaults else 0.7
        default_max_tokens = gen_defaults.max_output_tokens if gen_defaults else 1024

        request_kwargs = {
            "temperature": kwargs.get("temperature", default_temp),
            "max_tokens": kwargs.get("max_tokens", default_max_tokens),
        }
        request_kwargs.update(
            {k: v for k, v in kwargs.items() if k not in request_kwargs}
        )

        try:
            # create_with_completion returns a tuple (pydantic_obj, raw_response)
            (
                resp,
                raw_response,
            ) = await instructor_client.chat.completions.create_with_completion(
                model=self.default_model,
                messages=messages,
                response_model=response_model,
                max_retries=max_retries,
                **request_kwargs,
            )

            # Record token usage from the raw response
            if hasattr(raw_response, "usage") and raw_response.usage:
                self.record_token_usage(
                    prompt_tokens=raw_response.usage.prompt_tokens,
                    completion_tokens=raw_response.usage.completion_tokens,
                )

            return resp

        except openai.APIError as e:
            self._handle_openai_error(e)
            raise ProviderError(f"OpenAI API error: {e}") from e
        except ValidationError as e:
            raise StructuredOutputError(
                response_model.__name__,
                f"Failed to parse after retries: {e}",
            ) from e
        except Exception as e:
            raise ProviderError(
                f"Unexpected error in OpenAI structured gen: {e}"
            ) from e

    def _handle_openai_error(self, e: Exception) -> None:
        """
        Maps OpenAI SDK errors to standardized Athomic exceptions.

        Args:
            e: The original exception raised by the SDK.
        """
        if isinstance(e, openai.RateLimitError):
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}") from e

        if isinstance(e, openai.AuthenticationError):
            raise AuthenticationError(f"OpenAI authentication failed: {e}") from e

        if isinstance(e, openai.BadRequestError):
            if "context_length" in str(e):
                raise ContextWindowExceededError(
                    model=self.default_model, token_count=0, limit=0
                ) from e
            raise InvalidRequestError(f"Invalid request to OpenAI: {e}") from e

        # Generic APIError is handled by the caller or wrapped in ProviderError
