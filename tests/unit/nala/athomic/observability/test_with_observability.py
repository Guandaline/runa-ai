# tests/unit/nala/athomic/observability/test_with_observability.py
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.trace import StatusCode

from nala.athomic.observability.decorators.with_observability import with_observability


@pytest.fixture
def mock_dependencies():
    """Fixture that provides mocked dependencies for observability tests."""
    mock_span = MagicMock()

    tracer_mock = MagicMock()

    sync_context_manager = MagicMock()
    sync_context_manager.__enter__.return_value = mock_span
    tracer_mock.start_as_current_span.return_value = sync_context_manager

    tracer_mock.start_span.return_value = mock_span

    mock_trace_module = MagicMock()
    mock_context_module = MagicMock()

    mocks = {
        "tracer": patch(
            "nala.athomic.observability.decorators.with_observability.get_tracer",
            return_value=tracer_mock,
        ),
        "logger": patch(
            "nala.athomic.observability.decorators.with_observability.get_logger",
            return_value=MagicMock(),
        ),
        "request_id": patch(
            "nala.athomic.observability.decorators.with_observability.get_request_id",
            return_value="req-test",
        ),
        "trace_id": patch(
            "nala.athomic.observability.decorators.with_observability.get_trace_id",
            return_value="trace-test",
        ),
        "opentelemetry_trace": patch(
            "nala.athomic.observability.decorators.with_observability.trace",
            mock_trace_module,
        ),
        "opentelemetry_context": patch(
            "nala.athomic.observability.decorators.with_observability.context",
            mock_context_module,
        ),
        "span": mock_span,
    }
    return mocks


def test_sync_function_success(mock_dependencies):
    """Tests if the synchronous decorator works correctly in case of success."""
    with (
        mock_dependencies["tracer"],
        mock_dependencies["logger"] as logger_mock,
        mock_dependencies["request_id"],
        mock_dependencies["trace_id"],
    ):

        @with_observability(log_args=True, should_log_result=True)
        def sync_sum(a, b):
            return a + b

        result = sync_sum(5, 10)

        assert result == 15

        expected_call_extra = {
            "args": (5, 10),
            "kwargs": {},
            "trace_id": "trace-test",
            "request_id": "req-test",
        }
        logger_mock().info.assert_any_call("sync_sum called", extra=expected_call_extra)

        mock_dependencies["span"].set_status.assert_called_with(StatusCode.OK)


@pytest.mark.asyncio
async def test_async_function_exception(mock_dependencies):
    """Tests if the asynchronous decorator captures exceptions, logs, and updates the span status."""
    with (
        mock_dependencies["tracer"],
        mock_dependencies["logger"] as logger_mock,
        mock_dependencies["request_id"],
        mock_dependencies["trace_id"],
        mock_dependencies["opentelemetry_trace"],
        mock_dependencies["opentelemetry_context"] as mock_context,
    ):
        test_exception = ValueError("Something went wrong")

        @with_observability()
        async def failing_async_func():
            raise test_exception

        with pytest.raises(ValueError, match="Something went wrong"):
            await failing_async_func()

        # Assert
        mock_span = mock_dependencies["span"]
        logger_mock().error.assert_called_once()
        assert "failing_async_func error" in logger_mock().error.call_args.args[0]

        mock_span.record_exception.assert_called_once_with(test_exception)
        mock_span.set_status.assert_called_once_with(
            StatusCode.ERROR, description=str(test_exception)
        )

        mock_context.attach.assert_called_once()
        mock_context.detach.assert_called_once()


def test_log_args_and_result_can_be_disabled(mock_dependencies):
    """Tests if logging can be disabled via decorator parameters."""
    with (
        mock_dependencies["tracer"],
        mock_dependencies["logger"] as logger_mock,
    ):

        @with_observability(log_args=False, should_log_result=False)
        def silent_func():
            return "ok"

        silent_func()
        logger_mock().info.assert_not_called()
