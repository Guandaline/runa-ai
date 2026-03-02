# retry/decorator.py
import asyncio
import functools
from typing import Callable, Optional

from .handler import RetryHandler
from .policy import RetryPolicy


def retry(
    *,
    policy: Optional[RetryPolicy] = None,
    operation_name: Optional[str] = None,
    on_retry: Optional[Callable] = None,
    on_fail: Optional[Callable] = None,
    circuit_breaker_hook: Optional[Callable[[BaseException], None]] = None,
    logger: Optional[Callable] = None,
    tracer: Optional[Callable] = None,
):
    """
    A decorator to add retry logic to synchronous or asynchronous functions, with optional hooks for retry, failure, circuit breaker, logging, and tracing.
    Args:
        policy (Optional[RetryPolicy]): The retry policy to use. If None, a default policy may be applied.
        operation_name (Optional[str]): An optional name for the operation, used for logging or tracing.
        on_retry (Optional[Callable]): Optional callback invoked on each retry attempt.
        on_fail (Optional[Callable]): Optional callback invoked when all retry attempts fail.
        circuit_breaker_hook (Optional[Callable[[BaseException], None]]): Optional callback invoked when a circuit breaker event occurs.
        logger (Optional[Callable]): Optional logger function for logging retry events.
        tracer (Optional[Callable]): Optional tracer function for tracing retry events.
    Returns:
        Callable: A decorator that wraps the target function with retry logic, supporting both sync and async functions.
    Usage:
        @retry(policy=my_policy, on_retry=my_on_retry)
        def my_function(...):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        handler = RetryHandler(
            policy=policy,
            operation_name=operation_name,
            on_retry=on_retry,
            on_fail=on_fail,
            circuit_breaker_hook=circuit_breaker_hook,
            tracer=tracer,
            logger=logger,
        )
        is_coroutine = asyncio.iscoroutinefunction(fn)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return handler.run(fn, *args, **kwargs)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            return await handler.arun(fn, *args, **kwargs)

        return async_wrapper if is_coroutine else sync_wrapper

    return decorator
