# File: nala/athomic/context/execution.py

from typing import Any, Dict, Optional

from nala.athomic.context import context_vars


class ExecutionContext:
    """A data class that provides a snapshot of the current execution context.

    This class consolidates all context variables (e.g., tenant_id, request_id,
    trace_id) from the `context_vars` module into a single, cohesive object.
    Its primary purpose is to offer a clean way to access context information
    and to capture the context at a specific point in time for propagation to
    background tasks or asynchronous events.

    Attributes:
        tenant_id (Optional[str]): The identifier for the current tenant.
        request_id (Optional[str]): The unique ID for the current request.
        trace_id (Optional[str]): The ID for the distributed trace.
        span_id (Optional[str]): The ID for the current span within a trace.
        user_id (Optional[str]): The identifier for the authenticated user.
        role (Optional[str]): The role of the authenticated user.
        locale (Optional[str]): The locale/language for the current request.
        source_ip (Optional[str]): The IP address of the original client.
        session_id (Optional[str]): The session identifier.
        correlation_id (Optional[str]): An ID to correlate logs and events across services.
        feature_flags (Optional[Dict[str, bool]]): A dictionary of active feature flags.
    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        locale: Optional[str] = None,
        source_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        feature_flags: Optional[Dict[str, bool]] = None,
    ):
        """Initializes the ExecutionContext.

        If a value for a parameter is not explicitly provided, the constructor
        will fetch the current value from the global `context_vars`. This allows
        for both creating a snapshot of the current context (`ExecutionContext()`)
        and creating a custom context for specific purposes (like testing or
        background jobs).

        Args:
            tenant_id (Optional[str]): The unique identifier for the tenant.
            request_id (Optional[str]): The unique ID for the request.
            trace_id (Optional[str]): The distributed trace ID.
            span_id (Optional[str]): The current span ID.
            user_id (Optional[str]): The identifier for the user.
            role (Optional[str]): The user's role.
            locale (Optional[str]): The request's locale.
            source_ip (Optional[str]): The client's IP address.
            session_id (Optional[str]): The session ID.
            correlation_id (Optional[str]): The correlation ID.
            feature_flags (Optional[Dict[str, bool]]): A dictionary of feature flags.
        """
        self.tenant_id = tenant_id or context_vars.get_tenant_id()
        self.request_id = request_id or context_vars.get_request_id()
        self.trace_id = trace_id or context_vars.get_trace_id()
        self.span_id = span_id or context_vars.get_span_id()
        self.user_id = user_id or context_vars.get_user_id()
        self.role = role or context_vars.get_role()
        self.locale = locale or context_vars.get_locale()
        self.source_ip = source_ip or context_vars.get_source_ip()
        self.session_id = session_id or context_vars.get_session_id()
        self.correlation_id = correlation_id or context_vars.get_correlation_id()
        self.feature_flags = feature_flags or context_vars.get_feature_flags()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the context object to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the execution context,
            suitable for logging or propagating to other services.
        """
        return {
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "role": self.role,
            "locale": self.locale,
            "source_ip": self.source_ip,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "feature_flags": self.feature_flags,
        }

    def __repr__(self) -> str:
        """Returns a string representation of the object.

        Returns:
            str: A developer-friendly string representation of the context.
        """
        return f"ExecutionContext({self.to_dict()})"
