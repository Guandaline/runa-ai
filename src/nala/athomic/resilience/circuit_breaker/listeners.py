# src/nala/athomic/resilience/circuit_breaker/listeners.py
from typing import Any, Callable

import aiobreaker
from aiobreaker.state import CircuitBreakerBaseState, CircuitBreakerState

from nala.athomic.observability.log import get_logger
from nala.athomic.observability.metrics.usage.circuit_breaker_metrics import (
    circuit_breaker_calls_blocked_total,
    circuit_breaker_failures_recorded_total,
    circuit_breaker_state,
    circuit_breaker_state_changes_total,
)

logger = get_logger(__name__)

# Maps aiobreaker state names to numerical values for Prometheus Gauge
STATE_TO_GAUGE_VALUE = {
    "CLOSED": 0,
    "OPEN": 1,
    "HALF_OPEN": 2,
}


class LoggingCircuitBreakerListener(aiobreaker.CircuitBreakerListener):
    """
    A custom circuit breaker listener that provides comprehensive observability
    by logging state changes and updating Prometheus metrics.

    This listener is responsible for translating circuit breaker events into
    structured telemetry data.
    """

    def state_change(
        self,
        cb: aiobreaker.CircuitBreaker,
        old_state: CircuitBreakerBaseState,
        new_state: CircuitBreakerBaseState,
    ) -> None:
        """
        Called when the breaker's state changes (e.g., from CLOSED to OPEN).

        It logs the transition and updates the Prometheus Gauge tracking the state.
        """
        try:
            # Safely extract state names from the state classes
            old_name = CircuitBreakerState(old_state.__class__).name
            new_name = CircuitBreakerState(new_state.__class__).name
        except ValueError:
            # Fallback to class names if enum mapping fails
            old_name = old_state.__class__.__name__
            new_name = new_state.__class__.__name__

        logger.warning(
            f"Circuit breaker '{cb.name}' changed state from {old_name} to {new_name}"
        )

        # Increment metric for state changes
        circuit_breaker_state_changes_total.labels(
            circuit_name=cb.name, from_state=old_name, to_state=new_name
        ).inc()

        # Update the state gauge (0, 1, or 2)
        new_gauge_value = STATE_TO_GAUGE_VALUE.get(new_name, -1)
        circuit_breaker_state.labels(circuit_name=cb.name).set(new_gauge_value)

    def failure(self, cb: aiobreaker.CircuitBreaker, exc: Exception) -> None:
        """
        Called when a failure is recorded by the breaker.

        Args:
            cb (aiobreaker.CircuitBreaker): The circuit breaker instance.
            exc (Exception): The exception that caused the failure.
        """
        logger.info(
            f"Circuit breaker '{cb.name}' recorded failure ({type(exc).__name__}). "
            f"Fail count: {cb.fail_counter}, State: {cb.current_state}"
        )

        # Update metric for recorded failures
        circuit_breaker_failures_recorded_total.labels(circuit_name=cb.name).inc()

    def success(self, cb: aiobreaker.CircuitBreaker) -> None:
        """
        Called after a successful execution.

        It includes special logging when a success closes a HALF_OPEN circuit.

        Args:
            cb (aiobreaker.CircuitBreaker): The circuit breaker instance.
        """
        if cb.current_state == "HALF_OPEN":
            logger.info(
                f"Circuit breaker '{cb.name}' recorded success in HALF_OPEN state. Closing circuit."
            )
        else:
            logger.debug(f"Circuit breaker '{cb.name}' recorded success.")

    def thrown_error(self, cb: aiobreaker.CircuitBreaker, exc: Exception) -> None:
        """
        Called when a function call is blocked because the circuit is open.

        Args:
            cb (aiobreaker.CircuitBreaker): The circuit breaker instance.
            exc (Exception): The exception raised (always a `CircuitBreakerError`
                             in this context).
        """
        if isinstance(exc, aiobreaker.CircuitBreakerError):
            logger.error(
                f"Call blocked by open circuit breaker '{cb.name}'.",
                exc_info=False,
            )
            # Track metric for blocked calls
            circuit_breaker_calls_blocked_total.labels(circuit_name=cb.name).inc()

    def before_call(
        self,
        cb: aiobreaker.CircuitBreaker,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Placeholder for logic before function call. Currently ignored."""
        pass

    def after_call(
        self,
        cb: aiobreaker.CircuitBreaker,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ):
        """Placeholder for logic after function call. Currently ignored."""
        pass


global_logging_listener = LoggingCircuitBreakerListener()
