# tests/unit/nala/api/middleware/test_request_context_middleware.py
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.responses import Response

# Import the refactored middleware and the context_vars public API
from nala.api.middleware.request_context_middleware import RequestContextMiddleware
from nala.athomic.context import context_vars

# Path to the logger used inside the middleware module for patching
MIDDLEWARE_LOGGER_PATH = "nala.api.middleware.request_context_middleware.logger"


@pytest.fixture
def middleware() -> RequestContextMiddleware:
    """Provides a fresh instance of the middleware for each test."""
    # The 'app' argument is not used by the dispatch logic, so it can be None.
    return RequestContextMiddleware(app=None)


@pytest.fixture
def mock_request() -> MagicMock:
    """Provides a mock FastAPI Request object with a default state."""
    request = MagicMock()
    request.state = MagicMock()
    # Ensure 'user' attribute exists but is None by default
    request.state.user = None
    request.headers = {"user-agent": "pytest-test-client"}
    # Mock the OTEL span that might be attached by instrumentation
    request.scope = {
        "otel_span": MagicMock(
            get_span_context=MagicMock(
                return_value=MagicMock(trace_id=12345678901234567890)
            )
        )
    }
    return request


@pytest.fixture
def mock_call_next() -> AsyncMock:
    """Provides a mock for the 'call_next' function that returns a simple response."""
    _mock = AsyncMock()
    mock_response = Response(status_code=200, content=b"OK")
    # The real response object headers are mutable, so we don't need a mock for them
    _mock.return_value = mock_response
    return _mock


@pytest.mark.asyncio
class TestRequestContextMiddleware:
    """Test suite for the refactored RequestContextMiddleware."""

    async def test_dispatch_sets_context_correctly_with_full_user_payload(
        self,
        middleware: RequestContextMiddleware,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ):
        """
        Scenario: A request is made with a full user payload (including tenant_id).
        Verifies: All context variables are correctly set within the request and cleared after.
        """
        # Arrange
        request_id_from_header = f"req-{uuid.uuid4()}"
        tenant_id_from_payload = f"tenant-{uuid.uuid4()}"

        mock_request.headers = {"X-Request-ID": request_id_from_header}
        mock_request.state.user = {
            "sub": "user-123",
            "tenant_id": tenant_id_from_payload,
        }

        async def call_next_with_checks(request: MagicMock):
            # Assertions inside the 'call_next' to check context during the request
            assert context_vars.get_request_id() == request_id_from_header
            assert context_vars.get_tenant_id() == tenant_id_from_payload
            assert context_vars.get_trace_id() is not None
            return await mock_call_next(request)

        # Act
        response = await middleware.dispatch(mock_request, call_next_with_checks)

        # Assert
        # 1. Check response headers
        assert response.headers["X-Request-ID"] == request_id_from_header
        assert "X-Trace-ID" in response.headers

        # 2. Check that context is cleared after the request
        assert context_vars.get_request_id() is None
        assert context_vars.get_tenant_id() is None
        assert context_vars.get_trace_id() is None

    async def test_dispatch_generates_request_id_if_missing(
        self,
        middleware: RequestContextMiddleware,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ):
        """
        Scenario: The incoming request does not have an X-Request-ID header.
        Verifies: A new UUID is generated and used for the context and response header.
        """
        # Arrange (no X-Request-ID in headers)
        mock_request.headers = {}
        generated_id = None

        async def call_next_with_checks(request: MagicMock):
            nonlocal generated_id
            generated_id = context_vars.get_request_id()
            assert generated_id is not None
            return await mock_call_next(request)

        # Act
        response = await middleware.dispatch(mock_request, call_next_with_checks)

        # Assert
        assert response.headers["X-Request-ID"] == generated_id

    @patch(MIDDLEWARE_LOGGER_PATH)
    async def test_dispatch_logs_warning_if_tenant_id_is_missing_in_payload(
        self,
        mock_logger: MagicMock,
        middleware: RequestContextMiddleware,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ):
        """
        Scenario: The user is authenticated, but the JWT payload is missing the 'tenant_id' claim.
        Verifies: The tenant_id context is set to None, and a warning is logged.
        """
        # Arrange
        mock_request.state.user = {"sub": "user-no-tenant"}  # No tenant_id claim

        async def call_next_with_checks(request: MagicMock):
            assert context_vars.get_tenant_id() is None
            return await mock_call_next(request)

        # Act
        await middleware.dispatch(mock_request, call_next_with_checks)

        # Assert
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        assert "[TenantContext] User authenticated" in log_message
        assert "'tenant_id' claim is missing" in log_message
        assert "sub=user-no-tenant" in log_message

    async def test_dispatch_handles_no_user_payload_gracefully(
        self,
        middleware: RequestContextMiddleware,
        mock_request: MagicMock,
        mock_call_next: AsyncMock,
    ):
        """
        Scenario: The request has no authenticated user.
        Verifies: tenant_id is set to None and no errors occur.
        """
        # Arrange
        mock_request.state.user = None

        async def call_next_with_checks(request: MagicMock):
            assert context_vars.get_tenant_id() is None
            return await mock_call_next(request)

        # Act & Assert (test passes if no exception is raised)
        await middleware.dispatch(mock_request, call_next_with_checks)
