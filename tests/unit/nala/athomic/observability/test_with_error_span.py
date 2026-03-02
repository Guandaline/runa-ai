import asyncio
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.trace import StatusCode

from nala.athomic.observability.decorators.with_error_span import (
    with_span_and_error_capture,
)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_sync_function_error_is_captured():
    mock_span_ctx = MagicMock()
    mock_span = MagicMock()
    mock_span_ctx.__enter__.return_value = mock_span
    tracer_mock = MagicMock(start_as_current_span=MagicMock(return_value=mock_span_ctx))

    with (
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_tracer",
            return_value=tracer_mock,
        ),
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_request_id",
            return_value="req-sync",
        ),
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_trace_id",
            return_value="trace-sync",
        ),
    ):

        @with_span_and_error_capture("test_sync_error")
        def fail_func():
            raise RuntimeError("fail!")

        with pytest.raises(RuntimeError):
            fail_func()

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once_with(StatusCode.ERROR)


@pytest.mark.asyncio
async def test_async_function_error_is_captured():
    mock_span_ctx = MagicMock()
    mock_span = MagicMock()
    mock_span_ctx.__aenter__.return_value = mock_span

    async def fake_aexit(exc_type, exc_val, exc_tb):
        await asyncio.sleep(0)  # Simulate async context exit
        return False

    mock_span_ctx.__aexit__.side_effect = fake_aexit

    tracer_mock = MagicMock(start_as_current_span=MagicMock(return_value=mock_span_ctx))

    with (
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_tracer",
            return_value=tracer_mock,
        ),
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_request_id",
            return_value="req-async",
        ),
        patch(
            "nala.athomic.observability.decorators.with_error_span.get_trace_id",
            return_value="trace-async",
        ),
    ):

        @with_span_and_error_capture("test_async_error")
        async def fail_async():
            raise ValueError("async boom")

        with pytest.raises(ValueError):
            await fail_async()

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once_with(StatusCode.ERROR)
