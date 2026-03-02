# src/nala/athomic/performance/cache/handlers/cache_handler.py
import asyncio
import time
from typing import Any, Callable, Dict, Optional, Set, Tuple

from nala.athomic.observability.log import get_logger
from nala.athomic.observability.metrics.usage import (
    cache_background_refreshes_total,
    cache_error_counter,
    cache_hit_counter,
    cache_miss_counter,
    cache_stale_hits_total,
)
from nala.athomic.resilience.locking.factory import LockingFactory

from ..cache_key_resolver import CacheKeyGenerator
from ..protocol import CacheProtocol, ContextualKeyResolverType
from ..utils import apply_jitter

logger = get_logger(__name__)


class CacheHandler:
    """
    Orchestrates the read and compute logic for a function decorated with @cache_result.

    This handler implements multiple caching strategies: Cache-Aside, Refresh-Ahead,
    Jitter for stampedes, and distributed locking (Single-Flight).
    """

    def __init__(
        self,
        func: Callable,
        args: Tuple,
        kwargs: Dict,
        ttl: int,
        provider: CacheProtocol,
        use_jitter: Optional[bool] = False,
        use_lock: Optional[bool] = False,
        lock_timeout: Optional[int] = 30,
        key_resolver: Optional[ContextualKeyResolverType] = None,
        key_prefix: Optional[str] = None,
        refresh_ahead: Optional[bool] = False,
        refresh_threshold: Optional[float] = None,
        ttl_key: Optional[str] = None,
    ):
        """
        Initializes the handler with all parameters required for cache execution
        and resilience mechanisms.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.provider = provider
        self.use_jitter = use_jitter
        self.use_lock = use_lock
        self.lock_timeout = lock_timeout
        self.refresh_ahead = refresh_ahead
        self.refresh_threshold = refresh_threshold
        self.key_resolver = key_resolver
        self.key_prefix = key_prefix

        # Internal attribute to track background tasks created by refresh-ahead
        if not hasattr(CacheHandler, "_bg_tasks"):
            CacheHandler._bg_tasks: Set[asyncio.Task] = set()

        # Dynamic TTL resolution using Live Configuration (if configured)

        self.ttl = ttl

    async def _resolve_key(self) -> Optional[str]:
        """
        Resolves the cache key to use, delegating the logic to the generator.

        Ensures that only a single key is used, as @cache_result only supports one output.
        """
        resolved_keys = await CacheKeyGenerator.resolve_keys(
            func=self.func,
            args=self.args,
            kwargs=self.kwargs,
            key_resolver=self.key_resolver,
            key_prefix=self.key_prefix,
        )
        if len(resolved_keys) > 1:
            logger.error(
                f"The key_resolver for @cache_result in function '{self.func.__name__}' "
                f"returned multiple keys ({len(resolved_keys)}), but only one is allowed. Using the first."
            )
        return resolved_keys[0] if resolved_keys else None

    async def execute(self) -> Any:
        """Main entry point to execute the cache read strategy (Cache-Aside)."""
        self.logical_key = await self._resolve_key()
        if not self.logical_key:
            # Skip caching if key cannot be resolved
            return await self.func(*self.args, **self.kwargs)

        # 1. Attempt to read from cache
        try:
            cached_item = await self.provider.get(self.logical_key)
        except Exception as e:
            # Error reading from cache: treat as a miss and execute the miss flow
            logger.error(
                f"[Cache] Error reading from cache for key='{self.logical_key}': {e}"
            )
            cache_error_counter.labels(provider=self.provider.service_name).inc()
            return await self._trigger_miss_flow()

        # 2. Handle Cache Hit
        if cached_item is not None:
            cache_hit_counter.labels(provider=self.provider.service_name).inc()
            return await self._handle_cached_item(cached_item)

        # 3. Handle Cache Miss
        cache_miss_counter.labels(provider=self.provider.service_name).inc()
        return await self._trigger_miss_flow()

    async def _handle_cached_item(self, cached_item: Any) -> Any:
        """Handles logic for a valid or potentially stale cached item."""
        # Check if the cached item conforms to the expected envelope format
        if (
            isinstance(cached_item, dict)
            and "value" in cached_item
            and "expires_at" in cached_item
        ):
            stale_value = cached_item.get("value")
            expires_at = cached_item.get("expires_at")

            # Check for Refresh-Ahead condition (item is stale)
            if self.refresh_ahead and self._is_stale(expires_at):
                logger.debug(
                    f"[Cache] Stale value hit for key='{self.logical_key}'. Triggering background refresh."
                )

                cache_stale_hits_total.labels(
                    cache_key_prefix=self.key_prefix or "none"
                ).inc()

                # Start the refresh task in the background
                task = asyncio.create_task(self._background_refresh())
                self._bg_tasks.add(task)
                task.add_done_callback(self._bg_tasks.discard)

                # Return the old (stale) value immediately for low latency
                return stale_value
            else:
                return stale_value  # Return the value if not stale or if refresh is disabled
        else:
            # Invalid format: treat as a cache miss to force re-computation
            logger.warning(
                f"[Cache] Invalid cache item format for key='{self.logical_key}'. Recomputing."
            )
            return await self._trigger_miss_flow()

    def _is_stale(self, expires_at: Optional[float]) -> bool:
        """
        Checks if a cached item is close to expiring based on the defined
        refresh threshold (percentage of total TTL).
        """
        if not expires_at:
            return False

        time_to_expiry = expires_at - time.time()
        # Threshold calculation: percentage of the total TTL
        threshold_seconds = self.ttl * (self.refresh_threshold or 0)

        return time_to_expiry < threshold_seconds

    async def _trigger_miss_flow(self) -> Any:
        """Starts the cache miss flow, applying distributed locking if configured."""
        if self.use_lock:
            return await self._execute_with_lock()
        else:
            # Executes standard compute-and-store if no lock is needed
            return await self._compute_and_store()

    async def _background_refresh(self) -> None:
        """
        Executes the cache refresh logic in the background using a distributed
        lock to prevent the 'Thundering Herd' problem among services.
        """
        refresh_status = "failure"

        try:
            if self.use_lock:
                lock_provider = LockingFactory.create()
                lock_key = f"lock:{self.logical_key}"
                try:
                    # Acquire lock with a short timeout for the background task
                    async with lock_provider.acquire(
                        lock_key, timeout=self.lock_timeout
                    ):
                        logger.debug(
                            f"[Cache BG] Lock acquired for background refresh of key='{self.logical_key}'."
                        )
                        await self._compute_and_store()
                        refresh_status = "success"
                except asyncio.TimeoutError:
                    logger.warning(
                        f"[Cache BG] Could not acquire lock for background refresh of key='{self.logical_key}'. Another process is likely already refreshing."
                    )
            else:
                # If not using lock, just recompute (not recommended for critical paths)
                await self._compute_and_store()
                refresh_status = "success"
        except Exception as e:
            logger.error(
                f"[Cache BG] Error during background refresh for key='{self.logical_key}': {e}"
            )
        finally:
            cache_background_refreshes_total.labels(
                cache_key_prefix=self.key_prefix or "none", status=refresh_status
            ).inc()

    async def _compute_and_store(self) -> Any:
        """Calls the original function, stores the result, and includes metadata."""
        logger.debug(
            f"[Cache] Miss/Expired key='{self.logical_key}'. Computing value..."
        )
        # Execute the original function logic
        result = await self.func(*self.args, **self.kwargs)

        # Apply jitter to TTL if configured (to prevent stampedes)
        final_ttl = apply_jitter(self.ttl) if self.use_jitter else self.ttl

        # Create the cache envelope with expiration timestamp
        expires_at = time.time() + final_ttl
        value_to_store = {"value": result, "expires_at": expires_at}

        try:
            await self.provider.set(self.logical_key, value_to_store, ttl=final_ttl)
            logger.debug(
                f"[Cache] Computed value stored for key='{self.logical_key}' (TTL: {final_ttl}s)."
            )
        except Exception as e:
            logger.error(
                f"[Cache] Failed to store value for key='{self.logical_key}': {e}"
            )

        return result

    async def _execute_with_lock(self) -> Any:
        """
        Implements the Single-Flight Caching pattern using a distributed lock
        to ensure only one thread/process computes the value during a cache miss
        (Thundering Herd protection).
        """
        lock_provider = LockingFactory.create()
        lock_key = f"lock:{self.logical_key}"

        try:
            async with lock_provider.acquire(lock_key, timeout=self.lock_timeout):
                logger.debug(
                    f"[Cache] Lock acquired for key='{self.logical_key}'. Re-checking cache..."
                )
                # Double-checked locking: Check cache again after acquiring the lock
                cached_item = await self.provider.get(self.logical_key)
                if cached_item is not None and isinstance(cached_item, dict):
                    logger.debug(f"[Cache] Hit after lock for key='{self.logical_key}'")
                    # Return the value computed by the process that held the lock first
                    return cached_item.get("value")

                # If still a miss, this process computes and stores the value
                return await self._compute_and_store()
        except asyncio.TimeoutError:
            # Timeout during lock acquisition: treat as a critical miss and execute the original function
            logger.error(
                f"[Cache] Timeout acquiring lock for key='{self.logical_key}'. Serving uncached."
            )
            return await self.func(*self.args, **self.kwargs)  # Fallback
