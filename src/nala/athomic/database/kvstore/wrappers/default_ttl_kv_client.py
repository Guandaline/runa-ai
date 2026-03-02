# src/nala/athomic/database/kvstore/wrappers/default_ttl_kv_client.py
from typing import Any, Dict, List, Mapping, Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.database.kvstore import (
    DefaultTTLWrapperSettings,
    KVStoreSettings,
)
from nala.athomic.observability import get_logger

from ..protocol import KVStoreProtocol
from .base import WrapperBase

logger = get_logger(__name__)


class DefaultTTLKvClient(WrapperBase):
    """A decorator (Wrapper) for the KVStore client that automatically applies a default Time-To-Live (TTL).

    This class intercepts the `set` operation and injects a configured default TTL
    if no explicit TTL is provided by the caller. It ensures that keys are automatically
    expired, preventing cache overflow and maintaining consistency.

    Attributes:
        default_ttl (Optional[int]): The default TTL in seconds extracted from configuration, or None.
    """

    def __init__(
        self,
        client: KVStoreProtocol,
        settings: Optional[KVStoreSettings] = None,
        wrapper_settings: Optional[DefaultTTLWrapperSettings] = None,
    ):
        """Initializes the wrapper, resolving the configured default TTL value.

        Args:
            client (KVStoreProtocol): The underlying KVStore client being wrapped.
            settings (Optional[KVStoreSettings]): Optional global KVStore settings.
            wrapper_settings (Optional[DefaultTTLWrapperSettings]): Specific settings for this wrapper instance.
        """
        super().__init__(client)
        # settings is resolved but mainly for context/fallback in the base class
        settings = settings or get_settings().database.kvstore
        self.settings = wrapper_settings
        default_ttl_seconds = self.settings.default_ttl_seconds
        self.default_ttl: Optional[int] = None

        if default_ttl_seconds is not None and default_ttl_seconds > 0:
            self.default_ttl = int(default_ttl_seconds)

        logger.debug(
            f"{self.__class__.__name__} initialized. Wrapping {type(client).__name__}. Default TTL: {self.default_ttl}s"
        )

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Sets a key-value pair, applying the default TTL if no explicit TTL is given.

        Args:
            key (str): The key of the item to set.
            value (Any): The value to store.
            ttl (Optional[int]): Explicit time-to-live in seconds provided by the caller.
            nx (bool): If True, set the key only if it does not already exist.

        Returns:
            bool: True if the operation was successful.
        """
        effective_ttl: Optional[int] = None
        if ttl is not None:
            if ttl > 0:
                # Prioritize explicit TTL provided by the caller
                effective_ttl = ttl
        elif self.default_ttl:
            # Fall back to the configured default TTL
            effective_ttl = self.default_ttl

        # Delegate the call to the underlying client with the resolved TTL
        return await super().set(key, value, ttl=effective_ttl, nx=nx)

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """Sets multiple key-value pairs, applying the default TTL if no explicit TTL is given.

        Args:
            mapping (Dict[str, Any]): The dictionary of keys and values.
            ttl (Optional[int]): Explicit time-to-live in seconds for the batch.
            nx (bool): If True, set keys only if they do not exist.

        Returns:
            Dict[str, bool]: The result map from the underlying client.
        """
        effective_ttl: Optional[int] = None
        if ttl is not None:
            if ttl > 0:
                effective_ttl = ttl
        elif self.default_ttl:
            effective_ttl = self.default_ttl

        return await super().set_many(mapping, ttl=effective_ttl, nx=nx)

    async def zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Delegates the zadd operation to the wrapped client."""
        return await super().zadd(key, mapping)

    async def zrem(self, key: str, members: list[str]) -> int:
        """Delegates the zrem operation to the wrapped client."""
        return await super().zrem(key, members)

    async def zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Delegates the zpopbyscore operation to the wrapped client."""
        return await super().zpopbyscore(key, max_score)

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """Delegates the zrangebyscore operation to the wrapped client."""
        return await super().zrangebyscore(key, min_score, max_score)
