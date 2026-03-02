# src/nala/athomic/ai/cognitive/base.py
import time
from abc import ABC, abstractmethod
from typing import Optional

from opentelemetry.trace import SpanKind, StatusCode

from nala.athomic.ai.cognitive.protocol import CognitiveProtocol
from nala.athomic.ai.schemas.cognitive import IntentClassification
from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)
from nala.athomic.observability import get_logger
from nala.athomic.observability.metrics.usage.ai import (
    cognitive_classification_duration_seconds,
    cognitive_classification_total,
    cognitive_confidence_score,
    cognitive_intent_detected_total,
)
from nala.athomic.services.base import BaseService

logger = get_logger(__name__)


class CognitiveBaseService(BaseService, CognitiveProtocol, ABC):
    """
    Abstract Base Service for Cognitive Intent Classification.

    Implements standard observability (Prometheus Metrics + OTel Tracing)
    and lifecycle management.
    """

    def __init__(self, service_name: str, settings: CognitiveSettings):
        super().__init__(service_name=service_name, enabled=settings.enabled)
        self.settings = settings
        # Pre-bind metrics labels that are constant for this instance
        self._provider_label = service_name
        self._strategy_label = settings.strategy

    async def classify(
        self, query: str, history_context: Optional[str] = None
    ) -> IntentClassification:
        """
        Public API for intent classification with auto-instrumentation.
        """
        if not self.is_ready():
            await self.wait_ready()

        start_time = time.perf_counter()

        with self.tracer.start_as_current_span(
            f"{self.service_name}.classify", kind=SpanKind.SERVER
        ) as span:
            span.set_attribute("cognitive.query_length", len(query))
            span.set_attribute("cognitive.strategy", self._strategy_label)

            try:
                # Delegate to concrete implementation
                result = await self._classify_impl(query, history_context)

                # --- Metrics Recording ---
                duration = time.perf_counter() - start_time

                # 1. Latency
                cognitive_classification_duration_seconds.labels(
                    provider=self._provider_label, strategy=self._strategy_label
                ).observe(duration)

                # 2. Throughput (Success)
                cognitive_classification_total.labels(
                    provider=self._provider_label,
                    strategy=self._strategy_label,
                    status="success",
                ).inc()

                # 3. Business Insight (Intent Distribution)
                cognitive_intent_detected_total.labels(
                    intent=result.primary_intent.value
                ).inc()

                # 4. Quality (Confidence)
                cognitive_confidence_score.labels(
                    provider=self._provider_label, strategy=self._strategy_label
                ).observe(result.confidence)

                # --- Tracing Attributes ---
                span.set_attribute("cognitive.intent", result.primary_intent.value)
                span.set_attribute("cognitive.confidence", result.confidence)
                span.set_status(StatusCode.OK)

                return result

            except Exception as e:
                # Metrics: Failure
                cognitive_classification_total.labels(
                    provider=self._provider_label,
                    strategy=self._strategy_label,
                    status="failure",
                ).inc()

                logger.error(f"Classification failed in {self.service_name}: {e}")
                span.record_exception(e)
                span.set_status(StatusCode.ERROR)
                raise

    @abstractmethod
    async def _classify_impl(
        self, query: str, history_context: Optional[str]
    ) -> IntentClassification:
        """
        Implementation-specific logic (LLM, ML, etc.).
        """
        ...
