# src/nala/athomic/resilience/circuit_breaker/service.py
import asyncio
from datetime import timedelta
from typing import Any, Callable, Coroutine, Dict

import aiobreaker

from nala.athomic.config.schemas.resilience import CircuitBreakerSettings
from nala.athomic.observability import get_logger, get_tracer
from nala.athomic.observability.tracing import SpanKind, StatusCode

from .listeners import global_logging_listener
from .storage_factory import CircuitBreakerStorageFactory

logger = get_logger(__name__)
tracer = get_tracer(__name__)


class CircuitBreakerService:
    """
    Manages and executes operations protected by the Circuit Breaker pattern.

    This service acts as the central factory and orchestrator for `aiobreaker.CircuitBreaker`
    instances. It lazily creates and caches a breaker for each unique circuit name,
    resolving its configuration (fail_max, reset_timeout) and distributed storage
    based on application settings.

    Attributes:
        settings (CircuitBreakerSettings): The configuration for the circuit breaker module.
        _breakers (Dict[str, aiobreaker.CircuitBreaker]): Cache of active circuit breaker instances.
    """

    def __init__(self, settings: CircuitBreakerSettings):
        """
        Initializes the CircuitBreakerService.

        Args:
            settings (CircuitBreakerSettings): Configuration for the circuit breaker module.
        """
        self.settings = settings
        self._breakers: Dict[str, aiobreaker.CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def _get_or_create_breaker(
        self, circuit_name: str
    ) -> aiobreaker.CircuitBreaker:
        """
        Retrieves a cached breaker instance or creates a new one if it does not exist.

        This method resolves specific settings (fail_max, reset_timeout) by
        prioritizing per-circuit configurations over global defaults.

        Args:
            circuit_name (str): The unique name of the circuit.

        Returns:
            aiobreaker.CircuitBreaker: The configured breaker instance.
        """
        async with self._lock:
            if circuit_name not in self._breakers:
                logger.debug(
                    f"Creating new Circuit Breaker instance for '{circuit_name}'"
                )

                # 1. Resolve distributed state storage
                storage = await CircuitBreakerStorageFactory.create(
                    circuit_name=circuit_name, settings=self.settings
                )

                # 2. Resolve specific configuration overrides
                specific_config = (
                    self.settings.circuits.get(circuit_name)
                    if self.settings.circuits
                    else None
                )

                # 3. Determine final thresholds
                fail_max = (
                    specific_config.fail_max
                    if specific_config and specific_config.fail_max is not None
                    else self.settings.default_fail_max
                )
                reset_timeout = (
                    specific_config.reset_timeout_sec
                    if specific_config and specific_config.reset_timeout_sec is not None
                    else self.settings.default_reset_timeout_sec
                )

                # 4. Instantiate and configure the breaker
                self._breakers[circuit_name] = aiobreaker.CircuitBreaker(
                    fail_max=fail_max,
                    timeout_duration=timedelta(seconds=reset_timeout),
                    state_storage=storage,
                    # Global listener provides tracing and metrics
                    listeners=[global_logging_listener],
                    name=circuit_name,
                )
            return self._breakers[circuit_name]

    async def execute(
        self,
        circuit_name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executes an asynchronous function protected by the specified circuit breaker.

        It automatically wraps the execution with an OpenTelemetry span and handles
        the `CircuitBreakerError` case for proper observability.

        Args:
            circuit_name (str): The name of the circuit to use.
            func (Callable): The asynchronous function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: The result of the executed function.

        Raises:
            aiobreaker.CircuitBreakerError: If the circuit is open and the call is blocked.
        """
        breaker = await self._get_or_create_breaker(circuit_name)
        with tracer.start_as_current_span(
            f"CircuitBreaker.execute:{circuit_name}", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("circuit_breaker.name", circuit_name)
            try:
                result = await breaker.call_async(func, *args, **kwargs)
                span.set_status(StatusCode.OK)
                return result
            except aiobreaker.CircuitBreakerError as e:
                # Mark the span as blocked, set error status, and re-raise the exception
                span.set_attribute("circuit_breaker.call_blocked", True)
                span.set_status(StatusCode.ERROR, description="Circuit breaker is open")
                raise e
