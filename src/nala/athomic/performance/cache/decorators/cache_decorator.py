# src/nala/athomic/performance/cache/decorators/cache_decorator.py
import functools
from typing import Any, Callable, Optional

from ..factory import CacheFallbackFactory
from ..handlers import CacheHandler
from ..protocol import CacheProtocol, ContextualKeyResolverType


def cache(
    ttl: int = 60,
    key_prefix: Optional[str] = None,
    key_resolver: Optional[ContextualKeyResolverType] = None,
    use_jitter: Optional[bool] = False,
    use_lock: Optional[bool] = False,
    lock_timeout: Optional[int] = 30,
    refresh_ahead: Optional[bool] = False,
    refresh_threshold: Optional[float] = None,
    provider: Optional[CacheProtocol] = None,
    ttl_key: Optional[str] = None,
) -> Callable[..., Any]:
    """
    Decorator to cache the result of an asynchronous function using the
    Cache-Aside, Single-Flight, and Refresh-Ahead strategies.

    It collects all configuration parameters and delegates the complex
    execution logic to the CacheHandler.

    Args:
        ttl: Time to live (in seconds) for the cached item. Can be overridden by ttl_key.
        key_prefix: Static prefix for the cache key (e.g., 'user_service:').
        key_resolver: Custom function, string, or list to generate contextual keys.
        use_jitter: If True, adds random variance to the TTL to prevent cache stampedes.
        use_lock: If True, enables distributed locking (Single-Flight Caching).
        lock_timeout: Timeout in seconds for acquiring the distributed lock.
        refresh_ahead: If True, enables the background refresh strategy (stale hit).
        refresh_threshold: Percentage of TTL (0.0 to 1.0) when the item is considered stale
                           and a background refresh should be triggered.
        provider: Optional explicit CacheProtocol instance (for testing). Defaults to
                  CacheFallbackFactory.create().
        ttl_key: Key name in Live Config to dynamically override the TTL.

    Returns:
        Callable: The decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Resolve the provider: use explicit provider or the resilient fallback chain
            effective_provider = provider or CacheFallbackFactory.create()

            # Delegate all complexity to the CacheHandler orchestrator
            handler = CacheHandler(
                func=func,
                args=args,
                kwargs=kwargs,
                ttl=ttl,
                provider=effective_provider,
                key_prefix=key_prefix,
                key_resolver=key_resolver,
                use_jitter=use_jitter,
                use_lock=use_lock,
                lock_timeout=lock_timeout,
                refresh_ahead=refresh_ahead,
                refresh_threshold=refresh_threshold,
                ttl_key=ttl_key,
            )

            return await handler.execute()

        return wrapper

    return decorator
