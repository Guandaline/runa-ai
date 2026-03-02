# src/nala/api/middleware/request_context_middleware.py
import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from opentelemetry.trace import Span
from starlette.middleware.base import BaseHTTPMiddleware

from nala.athomic.config.settings import get_settings
from nala.athomic.context import context_vars
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to establish and clear execution context for each request.

    It sets context variables like request_id, trace_id, and tenant_id
    and ensures they are cleared after the request is complete.
    """

    def _set_request_context(self, request: Request) -> str:
        """Sets the request_id context variable."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        context_vars.set_request_id(request_id)
        return request_id

    def _set_trace_context(self, request: Request) -> str:
        """Sets the trace_id context variable from OTEL span if available."""
        span: Optional[Span] = getattr(request.scope, "otel_span", None)
        trace_id = (
            span.get_span_context().trace_id if span else (uuid.uuid4().int >> 64)
        )
        trace_id_str = format(trace_id, "032x")
        context_vars.set_trace_id(trace_id_str)
        return trace_id_str

    def _set_tenant_context(self, request: Request) -> None:
        """Sets the tenant_id context variable from the authenticated user payload."""
        tenant_id: Optional[str] = None
        try:
            user_payload = getattr(request.state, "user", None)
            if user_payload and isinstance(user_payload, dict):
                tenant_id = user_payload.get("tenant_id")
                if tenant_id:
                    logger.info(f"[TenantContext] Tenant ID set from JWT: {tenant_id}")
                else:
                    logger.warning(
                        f"[TenantContext] User authenticated (sub={user_payload.get('sub', 'N/A')}) "
                        "but 'tenant_id' claim is missing in token."
                    )
        except Exception:
            logger.exception("[TenantContext] Error processing tenant ID context.")
        finally:
            context_vars.set_tenant_id(tenant_id)

    def _set_timeout_context(self) -> None:
        """Sets the request timeout deadline context variable."""
        try:
            default_timeout = get_settings().timeout
            if default_timeout and default_timeout > 0:
                deadline = time.monotonic() + default_timeout
                context_vars.set_timeout_deadline(deadline)
        except Exception as e:
            logger.warning("Could not set request timeout deadline from settings.")
            logger.exception(f"Error setting timeout context variable. {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main dispatch method. Sets up all context variables and guarantees cleanup.
        """
        try:
            # --- Setup Context ---
            request_id = self._set_request_context(request)
            trace_id = self._set_trace_context(request)
            self._set_tenant_context(request)
            self._set_timeout_context()

            # --- Process Request ---
            response = await call_next(request)

            # --- Enrich Response ---
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id

            return response

        finally:
            # --- Guaranteedd Cleanup ---
            # This single call now replaces all manual token management.
            context_vars.clear_all_context()
            logger.debug("[RequestContextMiddleware] All context variables cleared.")
