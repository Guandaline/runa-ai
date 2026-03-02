# src/nala/athomic/database/kvstore/wrappers/key_resolver_kv_client.py
from typing import Any, Dict, List, Mapping, Optional

from nala.athomic.config.schemas.context import ContextSettings
from nala.athomic.config.schemas.database.kvstore import KeyResolvingWrapperSettings
from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.context.generator import ContextKeyGenerator
from nala.athomic.database.kvstore.protocol import KVStoreProtocol

from .base import WrapperBase


class KeyResolvingKVClient(WrapperBase):
    """A decorator (Wrapper) for the KVStore client that dynamically resolves keys using a ContextKeyGenerator.

    This wrapper applies a contextual prefix (e.g., namespace, tenant ID, user ID)
    to the logical key provided by the caller before forwarding the operation to
    the underlying KV store. This is essential for supporting multi-tenancy and
    avoiding key collisions in shared storage systems.

    Attributes:
        resolver (ContextKeyGenerator): The utility used to generate context-aware keys.
    """

    def __init__(
        self,
        client: KVStoreProtocol,
        settings: Optional[KVStoreSettings] = None,
        wrapper_settings: Optional[KeyResolvingWrapperSettings] = None,
        context_settings: Optional[ContextSettings] = None,
    ) -> None:
        """Initializes the KeyResolvingKVClient and sets up the ContextKeyGenerator.

        Args:
            client (KVStoreProtocol): The underlying KVStore client being wrapped.
            settings (Optional[KVStoreSettings]): The global KVStore settings.
            wrapper_settings (Optional[KeyResolvingWrapperSettings]): Specific settings for this wrapper.
            context_settings (Optional[ContextSettings]): Optional settings for the key generator context.
        """
        super().__init__(client)
        self.settings = settings or KVStoreSettings()
        # Fallback logic for accessing wrapper settings
        self.wrapper_settings = wrapper_settings or self.settings.wrappers

        self.resolver = ContextKeyGenerator(
            namespace=self.wrapper_settings.namespace or "",
            settings=context_settings,
        )

    def _resolve(self, key: str) -> str:
        """Generates the final, context-aware key string."""
        return self.resolver.generate(key)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves a value after resolving the contextual key."""
        return await super().get(self._resolve(key))

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Sets a value after resolving the contextual key."""
        return await super().set(self._resolve(key), value, ttl=ttl, nx=nx)

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """Sets multiple values after resolving their contextual keys.

        It resolves all keys in the batch, forwards the operation to the client,
        and then maps the results back to the original keys so the caller
        remains agnostic of the prefixes.

        Args:
            mapping (Dict[str, Any]): A dictionary of logical key-value pairs.
            ttl (Optional[int]): Time-To-Live in seconds.
            nx (bool): If True, set only if the key does not exist.

        Returns:
            Dict[str, bool]: A map of logical keys to success status.
        """
        # Create mapping with resolved keys and keep track of reverse mapping
        resolved_mapping = {}
        reverse_key_map = {}

        for original_key, value in mapping.items():
            resolved_key = self._resolve(original_key)
            resolved_mapping[resolved_key] = value
            reverse_key_map[resolved_key] = original_key

        # Execute batch operation
        results = await super().set_many(resolved_mapping, ttl=ttl, nx=nx)

        # Translate results back to original keys
        final_results = {}
        for r_key, success in results.items():
            if r_key in reverse_key_map:
                original = reverse_key_map[r_key]
                final_results[original] = success

        return final_results

    async def delete(self, key: str) -> None:
        """Deletes a key after resolving the contextual key."""
        await super().delete(self._resolve(key))

    async def delete_many(self, keys: List[str]) -> int:
        """Deletes multiple keys after resolving their contextual keys.

        Args:
            keys (List[str]): The list of logical keys to delete.

        Returns:
            int: The number of keys successfully deleted.
        """
        resolved_keys = [self._resolve(k) for k in keys]
        return await super().delete_many(resolved_keys)

    async def exists(self, key: str) -> bool:
        """Checks for key existence after resolving the contextual key."""
        return await super().exists(self._resolve(key))

    async def zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Delegates the zadd operation after resolving the contextual key."""
        return await super().zadd(self._resolve(key), mapping)

    async def zrem(self, key: str, members: list[str]) -> int:
        """Delegates the zrem operation after resolving the contextual key."""
        return await super().zrem(self._resolve(key), members)

    async def zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Delegates the zpopbyscore operation after resolving the contextual key."""
        return await super().zpopbyscore(self._resolve(key), max_score)

    # --- Hashes (NEW) ---

    async def hset(self, key: str, field: str, value: Any) -> int:
        """Delegates the hset operation after resolving the contextual key."""
        return await super().hset(self._resolve(key), field, value)

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Delegates the hgetall operation after resolving the contextual key."""
        return await super().hgetall(self._resolve(key))

    async def hdel(self, key: str, fields: List[str]) -> int:
        """Delegates the hdel operation after resolving the contextual key."""
        return await super().hdel(self._resolve(key), fields)

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """Delegates the zrangebyscore operation after resolving the contextual key."""
        return await super().zrangebyscore(self._resolve(key), min_score, max_score)
