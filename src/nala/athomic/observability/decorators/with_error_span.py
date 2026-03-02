# src/nala/athomic/observability/tracing/decorators.py
import functools
import inspect
from typing import Any, Callable, Optional

from opentelemetry.trace import SpanKind, StatusCode

from nala.athomic.context.context_vars import get_request_id, get_trace_id

from ..tracing import get_tracer


def _build_span_attributes(
    func: Callable,
    args: tuple,
    kwargs: dict,
    static_attributes: Optional[dict],
    attributes_from_args: Optional[dict[str, str]],
) -> dict:
    """
    Constructs a dictionary of attributes for the OpenTelemetry span.

    Attributes are sourced from:
    1. Current execution context (request_id, trace_id).
    2. Static decorator arguments.
    3. Dynamic values extracted from the decorated function's arguments.
    """
    # Use inspect.signature to safely resolve arguments against default values
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

    return span_attributes


def _handle_exception(span: Any, exc: Exception) -> None:
    """
    Standardizes exception handling for OpenTelemetry spans.

    Records the exception on the current span, sets the status to ERROR,
    and re-raises the exception to maintain function contract.
    """
    span.record_exception(exc)
    span.set_status(StatusCode.ERROR)

    raise


def with_span_and_error_capture(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes_from_args: Optional[dict[str, str]] = None,
    static_attributes: Optional[dict[str, str]] = None,
) -> Callable[..., Any]:
    """
    A decorator that instruments a function (async or sync) with an
    OpenTelemetry tracing span and centralizes error handling.

    This ensures that all decorated business logic is visible in the
    distributed tracing system with proper context propagation and error logging.

    Args:
        name: Optional name for the span. Defaults to the decorated function's name.
        kind: The SpanKind (e.g., SERVER, CLIENT, CONSUMER, PRODUCER). Defaults to INTERNAL.
        attributes_from_args: A mapping of {function_arg_name: span_attribute_key}
                              to dynamically extract values from the call signature.
        static_attributes: A dictionary of static key/value pairs to add to the span.

    Returns:
        Callable: The decorator function that returns the wrapped function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            span_attributes = _build_span_attributes(
                func, args, kwargs, static_attributes, attributes_from_args
            )

            # Use async context manager for asynchronous span lifecycle
            async with tracer.start_as_current_span(
                span_name, kind=kind, attributes=span_attributes
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    # Centralized error management
                    _handle_exception(span, e)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            span_attributes = _build_span_attributes(
                func, args, kwargs, static_attributes, attributes_from_args
            )

            # Use standard context manager for synchronous span lifecycle
            with tracer.start_as_current_span(
                span_name, kind=kind, attributes=span_attributes
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    # Centralized error management
                    _handle_exception(span, e)

        # Return the appropriate wrapper based on the function type
        return async_wrapper if is_async else sync_wrapper

    return decorator
