# src/nala/athomic/resilience/circuit_breaker/decorator.py
import functools
import inspect
from typing import Any, Callable, Optional

from .factory import CircuitBreakerFactory


def circuit_breaker(name: Optional[str] = None) -> Callable[..., Any]:
    """
    Decorator to protect an asynchronous function with a Circuit Breaker pattern.

    This decorator ensures that calls to the decorated function are monitored
    for failures. If the failure rate exceeds a threshold, the circuit opens,
    and subsequent calls are blocked, failing fast to allow the system to recover.
    All execution and state logic are delegated to the central `CircuitBreakerService`.

    Args:
        name (Optional[str]): The unique name for this circuit. If None, the
                              fully qualified name of the decorated function (`func.__qualname__`) is used.

    Returns:
        Callable: The decorator function.

    Raises:
        TypeError: If the decorated function is not asynchronous.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                "The @circuit_breaker decorator only supports async functions."
            )

        # Use the provided name or the function's qualified name for the circuit identifier
        circuit_name = name or func.__qualname__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Lazily retrieve the singleton service instance
            circuit_breaker_service = CircuitBreakerFactory.create()

            # Delegate execution to the service
            return await circuit_breaker_service.execute(
                circuit_name, func, *args, **kwargs
            )

        return async_wrapper

    return decorator
