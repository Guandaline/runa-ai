from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from aiobreaker.state import CircuitBreakerError, CircuitClosedState, CircuitOpenState

from nala.athomic.resilience.circuit_breaker.listeners import (
    LoggingCircuitBreakerListener,
)

METRICS_PATH = "nala.athomic.resilience.circuit_breaker.listeners"


@pytest.fixture
def mock_breaker() -> MagicMock:
    breaker = MagicMock()
    breaker.name = "test_breaker"
    breaker.fail_counter = 3
    breaker.current_state = "OPEN"
    return breaker


@pytest.fixture
def listener() -> LoggingCircuitBreakerListener:
    return LoggingCircuitBreakerListener()


@patch(f"{METRICS_PATH}.circuit_breaker_calls_blocked_total")
@patch(f"{METRICS_PATH}.circuit_breaker_failures_recorded_total")
@patch(f"{METRICS_PATH}.circuit_breaker_state")
@patch(f"{METRICS_PATH}.circuit_breaker_state_changes_total")
@patch(f"{METRICS_PATH}.logger")
def test_state_change(
    mock_logger,
    mock_state_changes,
    mock_state_gauge,
    _mock_failures,
    _mock_blocked,
    listener,
    mock_breaker,
):
    old_state = CircuitClosedState("CLOSED")
    new_state = CircuitOpenState("OPEN")

    listener.state_change(mock_breaker, old_state, new_state)

    mock_logger.warning.assert_called_with(
        "Circuit breaker 'test_breaker' changed state from CLOSED to OPEN"
    )
    mock_state_changes.labels(
        circuit_name="test_breaker", from_state="CLOSED", to_state="OPEN"
    ).inc.assert_called_once()
    mock_state_gauge.labels(circuit_name="test_breaker").set.assert_called_once_with(1)


@patch(f"{METRICS_PATH}.logger")
@patch(f"{METRICS_PATH}.circuit_breaker_failures_recorded_total")
def test_failure(mock_failures, mock_logger, listener, mock_breaker):
    exc = ValueError("Something failed")
    listener.failure(mock_breaker, exc)

    mock_logger.info.assert_called_with(
        "Circuit breaker 'test_breaker' recorded failure (ValueError). Fail count: 3, State: OPEN"
    )
    mock_failures.labels(circuit_name="test_breaker").inc.assert_called_once()


@patch(f"{METRICS_PATH}.logger")
@patch(f"{METRICS_PATH}.circuit_breaker_calls_blocked_total")
def test_thrown_error_when_blocked(mock_blocked, mock_logger, listener, mock_breaker):
    reopen_time = datetime.now() + timedelta(seconds=30)
    exc = CircuitBreakerError("Circuit is open", reopen_time=reopen_time)

    listener.thrown_error(mock_breaker, exc)

    mock_logger.error.assert_called_with(
        "Call blocked by open circuit breaker 'test_breaker'.", exc_info=False
    )
    mock_blocked.labels(circuit_name="test_breaker").inc.assert_called_once()
