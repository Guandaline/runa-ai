# src/nala/athomic/performance/cache/decorators/invalidate_cache_decorator.py
import functools
from typing import Any, Callable, Optional

from ..factory import CacheFallbackFactory
from ..handlers import InvalidationHandler
from ..protocol import CacheProtocol, ContextualKeyResolverType


def invalidate_cache(
    key_prefix: Optional[str] = None,
    key_resolver: Optional[ContextualKeyResolverType] = None,
    provider: Optional[CacheProtocol] = None,
) -> Callable[..., Any]:
    """
    Decorator to invalidate cache after the decorated function is called.
    This decorator will call the `invalidate` method of the provided cache provider
    with the specified key prefix and context.
    Args:
        key_prefix: An optional prefix to use for the cache keys.
        key_resolver: An optional function to generate cache keys based on the function's context.
        provider: An optional cache provider to use for invalidation.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            effective_provider = provider or CacheFallbackFactory.create()

            handler = InvalidationHandler(
                func=func,
                args=args,
                kwargs=kwargs,
                key_prefix=key_prefix,
                key_resolver=key_resolver,
                provider=effective_provider,
            )
            await handler.invalidate()

            return result

        return wrapper

    return decorator
