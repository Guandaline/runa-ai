# src/nala/athomic/resilience/rate_limiter/providers/limits_provider.py
from typing import Optional

from limits import parse
from limits.aio.storage import MemoryStorage, RedisStorage, Storage
from limits.aio.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    RateLimiter,
)

from nala.athomic.config.schemas.resilience.rate_limiter.rate_limiter_config import (
    LimitsProviderSettings,
    RateLimiterSettings,
)

from ..base import RateLimiterBase


class LimitsRateLimiter(RateLimiterBase):
    """
    A flexible rate limiter provider that uses the external `limits` library.

    This provider acts as an adapter, allowing the framework to use different
    storage backends (`MemoryStorage`, `RedisStorage`) and strategies
    (`FixedWindowRateLimiter`, `MovingWindowRateLimiter`) based solely on the
    configuration settings, adhering to the Strategy and Adapter patterns.

    Attributes:
        storage (Storage): The backend storage implementation (in-memory or Redis).
        limiter (RateLimiter): The rate limiting strategy instance used for enforcement.
    """

    def __init__(self, settings: RateLimiterSettings):
        """
        Initializes the provider, instantiating the storage and strategy components.

        Args:
            settings (RateLimiterSettings): The rate limiter configuration.

        Raises:
            ValueError: If the Redis storage backend is selected but the URI is missing.
        """
        super().__init__(settings=settings, service_name="limits_rate_limiter")

        provider_settings: LimitsProviderSettings = settings.provider

        # 1. Instantiate the correct storage based on configuration
        self.storage: Storage
        if provider_settings.storage_backend == "redis":
            if not provider_settings.redis_storage_uri:
                raise ValueError(
                    "Redis storage backend requires a 'redis_storage_uri'."
                )
            self.storage = RedisStorage(uri=provider_settings.redis_storage_uri)
            self.logger.info("Rate limiter storage configured to use: Redis.")
        else:  # Default to memory
            self.storage = MemoryStorage()
            self.logger.info("Rate limiter storage configured to use: In-Memory.")

        # 2. Instantiate the correct strategy based on configuration
        self.limiter: RateLimiter
        if provider_settings.strategy == "moving-window":
            self.limiter = MovingWindowRateLimiter(self.storage)
        else:  # Default to fixed-window
            self.limiter = FixedWindowRateLimiter(self.storage)

        self.logger.info(
            f"Rate limiter strategy configured to use: {provider_settings.strategy}."
        )

    async def _connect(self) -> None:
        """
        Checks the connection, but only if the configured storage backend
        is network-dependent (like Redis).
        """
        # Checks if the underlying storage is RedisStorage and calls its `check` method
        if isinstance(self.storage, RedisStorage):
            self.logger.debug("Checking Redis connection for rate limiter...")
            await self.storage.check()
            self.logger.success("Redis connection for rate limiting is active.")
        else:
            self.logger.debug("In-memory storage requires no connection.")

    async def _close(self) -> None:
        """
        Closes the storage connection if the underlying storage implementation provides a close method.
        """
        if hasattr(self.storage, "close"):
            await self.storage.close()

    async def _allow(self, key: str, rate: str) -> bool:
        """
        Checks if the request is allowed by delegating the decision to the configured `limiter` strategy.

        Args:
            key (str): The identifier being checked.
            rate (str): The rate limit string (e.g., "5/second").

        Returns:
            bool: True if the request is allowed (and a token is consumed), False otherwise.
        """
        rate_limit_item = parse(rate)
        # The `hit` method encapsulates the strategy-specific logic (fixed or moving window)
        return await self.limiter.hit(rate_limit_item, key)

    async def _clear(self, key: str, rate: str) -> None:
        """
        Resets the limit for a specific key/rate combination in the underlying storage.

        Args:
            key (str): The identifier whose counter should be cleared.
            rate (str): The rate limit string rule associated with the key.
        """
        try:
            rate_limit_item = parse(rate)
            # The storage key is derived from the identifier and the rate rule
            storage_key = rate_limit_item.key_for(key)
            await self.storage.clear(storage_key)
        except Exception:
            self.logger.exception(f"Failed to clear Redis rate limit for key='{key}'.")

    async def _reset(self) -> None:
        """
        Resets ALL rate limit counters managed by this storage instance.

        WARNING: This operation can be destructive in a shared Redis environment.
        """
        self.logger.warning(
            "Resetting all rate limit counters in the configured Redis database."
        )
        await self.storage.reset()

    async def _get_current_usage(self, key: str, rate: str) -> Optional[int]:
        """
        Gets the current usage count for a key by calculating `amount - remaining_hits`.

        Args:
            key (str): The identifier to query.
            rate (str): The rate limit string rule.

        Returns:
            Optional[int]: The number of requests used in the current window.
        """
        try:
            rate_limit_item = parse(rate)
            # get_window_stats returns (reset_time, remaining_hits)
            _, remaining_hits = await self.limiter.get_window_stats(
                rate_limit_item, key
            )
            # Usage = Total Allowed - Remaining Hits
            return rate_limit_item.amount - remaining_hits
        except Exception:
            self.logger.exception(
                f"Could not get current usage for key='{key}' from Redis."
            )
            return None
