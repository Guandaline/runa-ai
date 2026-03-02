# src/nala/athomic/ai/agents/persistence/providers/base.py
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from nala.athomic.ai.agents.persistence.protocol import CheckpointProtocol
from nala.athomic.observability import get_logger, get_tracer
from nala.athomic.observability.metrics.usage import (
    agent_checkpoint_duration_seconds,
    agent_checkpoint_operations_total,
    agent_checkpoint_size_bytes,
)
from nala.athomic.observability.tracing import SpanKind, StatusCode
from nala.athomic.services.base import BaseService


class BaseCheckpoint(BaseService, CheckpointProtocol, ABC):
    """
    Abstract Base Class for Checkpoint Providers.

    Inherits from BaseService to participate in the application lifecycle
    (start/stop/ready management).

    Implements the Template Method pattern to enforce observability (metrics,
    logging, tracing) and error handling around the core persistence logic.
    """

    def __init__(self, backend_name: str) -> None:
        # Initialize BaseService with a unique logical name
        service_name = f"agent_persistence_{backend_name}"
        super().__init__(service_name=service_name)

        self.backend_name = backend_name
        # We get a specific logger for this domain
        self.logger = get_logger(f"ai.agents.persistence.{backend_name}")
        self.tracer = get_tracer(f"ai.agents.persistence.{backend_name}")

    async def save(self, thread_id: str, state: Dict[str, Any]) -> None:
        """
        Public template method for saving state. Handles observability.
        """
        start_time = time.perf_counter()
        status = "error"

        with self.tracer.start_as_current_span(
            "checkpoint.save", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("checkpoint.thread_id", thread_id)
            span.set_attribute("checkpoint.backend", self.backend_name)

            try:
                # Execute concrete implementation
                await self._save_impl(thread_id, state)

                status = "success"
                # Estimate size for metrics (naive string length approximation)
                size_approx = len(str(state))
                agent_checkpoint_size_bytes.labels(backend=self.backend_name).observe(
                    size_approx
                )

            except Exception as e:
                self.logger.error(
                    f"Failed to save checkpoint for thread {thread_id}: {e}"
                )
                span.record_exception(e)
                span.set_status(StatusCode.ERROR)
                raise
            finally:
                duration = time.perf_counter() - start_time
                agent_checkpoint_duration_seconds.labels(
                    operation="save", backend=self.backend_name
                ).observe(duration)
                agent_checkpoint_operations_total.labels(
                    operation="save", status=status, backend=self.backend_name
                ).inc()

    async def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Public template method for loading state. Handles observability.
        """
        start_time = time.perf_counter()
        status = "error"

        with self.tracer.start_as_current_span(
            "checkpoint.load", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("checkpoint.thread_id", thread_id)
            span.set_attribute("checkpoint.backend", self.backend_name)

            try:
                # Execute concrete implementation
                state = await self._load_impl(thread_id)

                status = "success"
                span.set_attribute("checkpoint.found", bool(state))
                return state

            except Exception as e:
                self.logger.error(
                    f"Failed to load checkpoint for thread {thread_id}: {e}"
                )
                span.record_exception(e)
                span.set_status(StatusCode.ERROR)
                raise
            finally:
                duration = time.perf_counter() - start_time
                agent_checkpoint_duration_seconds.labels(
                    operation="load", backend=self.backend_name
                ).observe(duration)
                agent_checkpoint_operations_total.labels(
                    operation="load", status=status, backend=self.backend_name
                ).inc()

    async def delete(self, thread_id: str) -> None:
        """Public template method for deleting state."""
        with self.tracer.start_as_current_span("checkpoint.delete"):
            try:
                await self._delete_impl(thread_id)
            except Exception as e:
                self.logger.error(f"Failed to delete checkpoint {thread_id}: {e}")
                raise

    # --- Abstract Methods (Contract for Subclasses) ---

    @abstractmethod
    async def _save_impl(self, thread_id: str, state: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def _load_impl(self, thread_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def _delete_impl(self, thread_id: str) -> None:
        pass
