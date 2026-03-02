# src/nala/athomic/observability/tracing/decorators_simple.py
import functools
import inspect
from typing import Any, Callable, Optional

from opentelemetry.trace import SpanKind

from nala.athomic.context.context_vars import get_request_id, get_trace_id
from nala.athomic.observability.tracing import get_tracer


def with_span(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes_from_args: Optional[dict[str, str]] = None,
    static_attributes: Optional[dict[str, Any]] = None,
) -> Callable[..., Any]:
    """
    Creates an OpenTelemetry span around the decorated function's execution.

    This decorator provides basic tracing instrumentation without automatic
    error capture or status setting, delegating that responsibility to the
    caller or a subsequent decorator (like `with_observability`).

    Args:
        name: Optional name for the span. Defaults to the decorated function's name.
        kind: The SpanKind (e.g., INTERNAL, SERVER, CLIENT, CONSUMER, PRODUCER).
        attributes_from_args: A mapping of {function_arg_name: span_attribute_key}
                              to dynamically extract values from the call signature.
                              Example: {"user_id": "user.id"}
        static_attributes: A dictionary of static key/value pairs to add to the span.

    Returns:
        Callable: The decorator function that returns the wrapped function.
    """

    def build_span_attributes(func: Callable, args: tuple, kwargs: dict) -> dict:
        """Constructs span attributes from context, static values, and function arguments."""
        # Safely bind arguments to resolve against default values
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        span_attributes = {
            "request.id": get_request_id(),
            "trace.id": get_trace_id(),
            **(static_attributes or {}),
        }

        if attributes_from_args:
            for arg_name, attr_name in attributes_from_args.items():
                if arg_name in bound_args.arguments:
                    span_attributes[attr_name] = bound_args.arguments[arg_name]

        return {k: v for k, v in span_attributes.items() if v is not None}

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            span_attributes = build_span_attributes(func, args, kwargs)
            tracer = get_tracer()

            # Start the span and activate it as the current span for the async context
            with tracer.start_as_current_span(
                span_name, kind=kind, attributes=span_attributes
            ):
                # The absence of try/except here is deliberate,
                # allowing the caller to handle exceptions.
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            span_attributes = build_span_attributes(func, args, kwargs)
            tracer = get_tracer()

            # Start the span and activate it as the current span for the sync context
            with tracer.start_as_current_span(
                span_name, kind=kind, attributes=span_attributes
            ):
                return func(*args, **kwargs)

        # Return the appropriate wrapper based on the function type
        return async_wrapper if is_async else sync_wrapper

    return decorator
