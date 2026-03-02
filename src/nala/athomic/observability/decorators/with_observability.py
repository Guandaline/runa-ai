# src/nala/athomic/observability/decorators.py
import functools
import inspect
from typing import Any, Callable, Dict, Optional

from opentelemetry import context, trace
from opentelemetry.trace import SpanKind, StatusCode

from nala.athomic.context.context_vars import get_request_id, get_trace_id
from nala.athomic.observability.log import get_logger
from nala.athomic.observability.tracing import get_tracer


def build_span_attributes(
    bound_args, static_attributes, attributes_from_args
) -> Dict[str, Any]:
    """Constructs OpenTelemetry span attributes from context and function arguments."""
    span_attributes = {
        "request.id": get_request_id(),
        "trace.id": get_trace_id(),
        **(static_attributes or {}),
    }
    if attributes_from_args:
        for arg_name, attr_name in attributes_from_args.items():
            if arg_name in bound_args.arguments:
                span_attributes[attr_name] = bound_args.arguments[arg_name]
    # Filter out None values before setting attributes on the span
    return {k: v for k, v in span_attributes.items() if v is not None}


def log_call(logger, func_name: str, args, kwargs) -> None:
    """Logs the function call, including arguments and execution context."""
    logger.info(
        f"{func_name} called",
        extra={
            "args": args,
            "kwargs": kwargs,
            "trace_id": get_trace_id(),
            "request_id": get_request_id(),
        },
    )


def log_result(logger, func_name: str, result) -> None:
    """Logs the function return value upon successful completion."""
    logger.info(
        f"{func_name} returned",
        extra={
            "result": result,
            "trace_id": get_trace_id(),
            "request_id": get_request_id(),
        },
    )


def log_error(logger, func_name: str, error: Exception) -> None:
    """Logs detailed exception information upon function failure."""
    logger.error(
        f"{func_name} error: {error}",
        extra={
            "trace_id": get_trace_id(),
            "request_id": get_request_id(),
        },
        exc_info=True,
    )


def _async_observability_wrapper(
    func,
    logger,
    name,
    kind,
    static_attributes,
    attributes_from_args,
    should_log_result,
    log_args,
):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = get_tracer()
        span_name = name or func.__name__
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()
        span_attributes = build_span_attributes(
            bound_args, static_attributes, attributes_from_args
        )

        if log_args:
            log_call(logger, func.__name__, args, kwargs)

        span = tracer.start_span(span_name, kind=kind, attributes=span_attributes)
        token = context.attach(trace.set_span_in_context(span))

        try:
            result = await func(*args, **kwargs)
            span.set_status(StatusCode.OK)
            if should_log_result:
                log_result(logger, func.__name__, result)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, description=str(e))
            log_error(logger, func.__name__, e)
            raise
        finally:
            span.end()
            context.detach(token)

    return wrapper


def _sync_observability_wrapper(
    func,
    logger,
    name,
    kind,
    static_attributes,
    attributes_from_args,
    should_log_result,
    log_args,
):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracer = get_tracer()
        span_name = name or func.__name__
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()
        span_attributes = build_span_attributes(
            bound_args, static_attributes, attributes_from_args
        )

        if log_args:
            log_call(logger, func.__name__, args, kwargs)

        with tracer.start_as_current_span(
            span_name, kind=kind, attributes=span_attributes
        ) as span:
            try:
                result = func(*args, **kwargs)
                span.set_status(StatusCode.OK)
                if should_log_result:
                    log_result(logger, func.__name__, result)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                log_error(logger, func.__name__, e)
                raise

    return wrapper


def with_observability(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes_from_args: Optional[Dict[str, str]] = None,
    static_attributes: Optional[Dict[str, Any]] = None,
    should_log_result: bool = True,
    log_args: bool = True,
) -> Callable[..., Any]:
    """
    A unified decorator for Observability that instruments a function with
    OpenTelemetry tracing and structured logging (call, result, error).

    This combines tracing and logging boilerplate into a single, declarative
    wrapper, adhering to Aspect-Oriented Programming (AOP).

    Args:
        name: Optional name for the span. Defaults to the decorated function's name.
        kind: The SpanKind (e.g., SERVER, CLIENT, CONSUMER, PRODUCER). Defaults to INTERNAL.
        attributes_from_args: A mapping of {function_arg_name: span_attribute_key}
                              to dynamically extract values from the call signature.
        static_attributes: A dictionary of static key/value pairs to add to the span.
        should_log_result: If True, logs the function's return value. Defaults to True.
        log_args: If True, logs the function's arguments upon call. Defaults to True.

    Returns:
        Callable: The decorator function that returns the wrapped function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)
        logger = get_logger(func.__module__)
        if is_async:
            return _async_observability_wrapper(
                func,
                logger,
                name,
                kind,
                static_attributes,
                attributes_from_args,
                should_log_result,
                log_args,
            )
        else:
            return _sync_observability_wrapper(
                func,
                logger,
                name,
                kind,
                static_attributes,
                attributes_from_args,
                should_log_result,
                log_args,
            )

    return decorator
