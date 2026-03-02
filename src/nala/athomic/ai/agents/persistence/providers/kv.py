# src/nala/athomic/ai/agents/persistence/providers/kv.py
from typing import Any, Dict, Optional

from nala.athomic.ai.agents.persistence.base import BaseCheckpoint
from nala.athomic.database.kvstore.protocol import KVStoreProtocol


class KVCheckpoint(BaseCheckpoint):
    """
    Checkpoint implementation using a Key-Value Store abstraction.

    This provider delegates serialization and storage to the injected KVStore.
    It expects the underlying KVStore implementation to handle data encoding.
    """

    def __init__(
        self,
        kv_store: KVStoreProtocol,
        namespace: str,
        ttl_seconds: int,
    ) -> None:
        super().__init__(backend_name="kv_store")
        self.kv_store = kv_store
        # Serializer is kept in __init__ signature for Factory compatibility
        # but not used for serialization logic here to avoid double-encoding.
        self.namespace = namespace
        self.ttl_seconds = ttl_seconds

    def _get_key(self, thread_id: str) -> str:
        """Constructs the namespaced key."""
        return f"{self.namespace}:{thread_id}"

    async def _save_impl(self, thread_id: str, state: Dict[str, Any]) -> None:
        """Saves state to KV store."""
        key = self._get_key(thread_id)

        await self.kv_store.set(key=key, value=state, ttl=self.ttl_seconds)

    async def _load_impl(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Fetches state from KV store."""
        key = self._get_key(thread_id)

        state = await self.kv_store.get(key)

        if state is None:
            return None

        return state

    async def _delete_impl(self, thread_id: str) -> None:
        """Removes the checkpoint key."""
        key = self._get_key(thread_id)
        await self.kv_store.delete(key)
