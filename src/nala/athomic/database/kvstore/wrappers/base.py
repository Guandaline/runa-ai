# src/nala/athomic/database/kvstore/wrappers/base.py

from typing import Any, Dict, List, Mapping, Optional

from nala.athomic.services.protocol import BaseServiceProtocol

from ..base import BaseKVStore
from ..protocol import KVStoreProtocol


class WrapperBase(KVStoreProtocol, BaseServiceProtocol):
    """Abstract base class for all Key-Value Store (KVStore) wrappers.

    This class provides the foundation for implementing the **Decorator Pattern**
    by implementing all methods of the `KVStoreProtocol` and `BaseServiceProtocol`
    through default delegation to the internal (wrapped) client. Concrete wrappers
    need only override the specific method(s) whose behavior they intend to modify.

    Attributes:
        client (BaseKVStore): The underlying client instance being wrapped.
    """

    def __init__(self, client: KVStoreProtocol):
        """Initializes the wrapper and validates the wrapped client.

        Args:
            client (KVStoreProtocol): The instance to be wrapped, which must implement the KVStoreProtocol.

        Raises:
            TypeError: If the wrapped client does not follow the KVStoreProtocol.
        """
        if not isinstance(client, (BaseServiceProtocol, KVStoreProtocol)):
            raise TypeError("The wrapped client must follow the KVStoreProtocol.")
        self.client: BaseKVStore = client

    # ----------------------------------------
    # --- Lifecycle Methods (Default Delegation) ---
    # ----------------------------------------

    @property
    def service_name(self) -> str:
        """Returns the service name of the underlying client."""
        return self.client.service_name

    async def connect(self) -> None:
        """Delegates the connection request to the wrapped client."""
        await self.client.connect()

    async def close(self) -> None:
        """Delegates the close request to the wrapped client."""
        await self.client.close()

    async def wait_ready(self) -> None:
        """Delegates the wait_ready request to the wrapped client."""
        await self.client.wait_ready()

    def is_ready(self) -> bool:
        """Checks the ready state of the wrapped client."""
        return self.client.is_ready()

    def is_closed(self) -> bool:
        """Checks the closed state of the wrapped client."""
        return self.client.is_closed()

    def is_enabled(self) -> bool:
        """Checks the enabled status of the wrapped client."""
        return self.client.is_enabled()

    # ----------------------------------------
    # --- Data Methods (Default Delegation) ---
    # ----------------------------------------

    async def get(self, key: str) -> Optional[Any]:
        """Delegates the get operation to the wrapped client."""
        return await self.client.get(key)

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Delegates the set operation to the wrapped client."""
        return await self.client.set(key, value, ttl=ttl, nx=nx)

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """Delegates set_many to the wrapped client."""
        return await self.client.set_many(mapping, ttl=ttl, nx=nx)

    async def delete(self, key: str) -> None:
        """Delegates the delete operation to the wrapped client."""
        await self.client.delete(key)

    async def delete_many(self, keys: List[str]) -> int:
        """Delegates delete_many to the wrapped client."""
        return await self.client.delete_many(keys)

    async def exists(self, key: str) -> bool:
        """Delegates the exists operation to the wrapped client."""
        return await self.client.exists(key)

    async def clear(self) -> None:
        """Delegates the clear operation to the wrapped client."""
        await self.client.clear()

    async def is_available(self) -> bool:
        """Delegates the is_available check to the wrapped client."""
        return await self.client.is_available()

    async def zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Delegates the zadd operation to the wrapped client."""
        return await self.client._zadd(key, mapping)

    async def zrem(self, key: str, members: list[str]) -> int:
        """Delegates the zrem operation to the wrapped client."""
        return await self.client._zrem(key, members)

    async def zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Delegates the zpopbyscore operation to the wrapped client."""
        return await self.client._zpopbyscore(key, max_score)

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """Delegates the zrangebyscore operation to the wrapped client."""
        return await self.client.zrangebyscore(key, min_score, max_score)

        # --- Hashes ---

    async def hset(self, key: str, field: str, value: Any) -> int:
        """Delegates the hset operation to the wrapped client."""
        return await self.client.hset(key, field, value)

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Delegates the hgetall operation to the wrapped client."""
        return await self.client.hgetall(key)

    async def hdel(self, key: str, fields: List[str]) -> int:
        """Delegates the hdel operation to the wrapped client."""
        return await self.client.hdel(key, fields)

    # ----------------------------------------
    # --- Native Client Methods (Default Delegation) ---
    # ----------------------------------------

    async def get_final_client(self) -> Any:
        """Returns the lowest-level raw client instance, delegating recursively."""
        # Recursively accesses until it finds the final client
        if hasattr(self.client, "get_final_client"):
            return await self.client.get_final_client()
        return self.client

    def get_sync_client(self) -> Any:
        """Returns the underlying raw synchronous client instance, delegating recursively."""
        return self.client.get_sync_client()
