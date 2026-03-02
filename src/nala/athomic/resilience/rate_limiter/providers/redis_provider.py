from typing import Optional

from nala.athomic.config import KVStoreSettings
from nala.athomic.config.schemas.resilience.rate_limiter.rate_limiter_config import (
    RateLimiterSettings,
)
from nala.athomic.database.kvstore.factory import KVStoreFactory
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.services.exceptions import ProviderInitializationError

from ..base import RateLimiterBase


class RedisRateLimiter(RateLimiterBase):
    """
    Rate limiter implementation based on a fixed-window algorithm,
    fully delegated to the KVStore abstraction.

    This provider does NOT know about Redis, Lua, or scripts.
    All backend-specific behavior is handled by the KVStore.
    """

    def __init__(
        self,
        settings: RateLimiterSettings,
        kv_store: Optional[KVStoreProtocol] = None,
    ):
        super().__init__(settings=settings, service_name="redis_rate_limiter")

        kvstore_settings: KVStoreSettings = settings.provider.kvstore

        self.kv_store: KVStoreProtocol = kv_store or KVStoreFactory.create(
            settings=kvstore_settings
        )

    async def _connect(self) -> None:
        """
        Ensures the KVStore is connected and ready.
        """
        self.logger.debug("Connecting rate limiter via KVStore...")

        try:
            await self.kv_store.connect()
            await self.kv_store.wait_ready()
        except Exception as exc:
            raise ProviderInitializationError(
                self.service_name,
                f"KVStore connection failed: {exc}",
            ) from exc

        self.logger.success("Rate limiter is connected via KVStore.")

    async def _close(self) -> None:
        """
        No-op. KVStore lifecycle is managed globally.
        """
        self.logger.debug("Closing RedisRateLimiter (no-op).")

    async def _allow(self, key: str, rate: str) -> bool:
        """
        Checks whether a hit is allowed using a fixed-window algorithm
        executed by the KVStore backend.
        """
        try:
            amount, seconds = map(int, rate.split("/"))
        except (ValueError, TypeError):
            self.logger.error(
                f"Invalid rate format '{rate}'. Expected 'amount/seconds'."
            )
            return False

        try:
            result = await self.kv_store.execute_script(
                name="rate_limit",
                keys=[key],
                args=[str(amount), str(seconds)],
            )
            return result == 1

        except Exception:
            self.logger.exception(
                f"KVStore error during rate limit check for key='{key}'. Denying request."
            )
            return False

    async def _clear(self, key: str, rate: str) -> None:
        """
        Clears the rate limit state for a given key.
        """
        try:
            await self.kv_store.delete(key)
        except Exception:
            self.logger.exception(f"Failed to clear rate limit key='{key}'. Ignoring.")

    async def _reset(self) -> None:
        """
        Global reset is intentionally not supported.
        """
        self.logger.warning("Global reset is not supported for RedisRateLimiter.")
        raise NotImplementedError("Global reset is not supported by this provider.")

    async def _get_current_usage(self, key: str, rate: str) -> Optional[int]:
        """
        Retrieves the current usage counter for a key.
        """
        try:
            value = await self.kv_store.get(key)
            if value is None:
                return 0
            return int(value)
        except Exception:
            return None
