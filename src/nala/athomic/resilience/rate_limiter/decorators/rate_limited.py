# src/nala/athomic/resilience/rate_limiter/decorators/rate_limited.py
import functools
from typing import Any, Awaitable, Callable

from ..exceptions import RateLimitExceeded
from ..service import rate_limiter_service


def rate_limited(policy: str) -> Callable[..., Awaitable[Any]]:
    """
    Decorator that applies the **Rate Limiting** pattern to an asynchronous function.

    It delegates the entire enforcement logic to the central `RateLimiterService`.
    If the limit is exceeded, it raises a specific exception instead of executing
    the decorated function.

    Args:
        policy (str): The name of the rate limit policy to apply (e.g., 'default', 'heavy_users'),
                      as defined in the configuration.

    Returns:
        Callable: The decorator function.

    Raises:
        RateLimitExceeded: If the request is blocked by the rate limiter.
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # The logical key is composed of the function's fully qualified name
            logical_key = func.__qualname__

            # Delegate the actual check (lookup, decrement, status update) to the service
            is_allowed = await rate_limiter_service.check(policy, logical_key)

            if is_allowed:
                return await func(*args, **kwargs)
            else:
                # Raise a specific exception upon rejection
                raise RateLimitExceeded(key=logical_key, limit=policy)

        return wrapper

    return decorator
