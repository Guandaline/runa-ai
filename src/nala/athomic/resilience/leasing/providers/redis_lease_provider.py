from datetime import datetime, timezone
from typing import Optional

import orjson

from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.resilience.leasing.exceptions import LeaseError
from nala.athomic.resilience.leasing.models import Lease
from nala.athomic.resilience.leasing.protocol import LeaseProtocol


class RedisLeaseProvider(LeaseProtocol):
    """
    Redis-backed lease provider.

    Implements lease acquisition, renewal and release
    using the KVStore abstraction.
    """

    def __init__(self, kv_store: KVStoreProtocol):
        self.kv_store = kv_store

    async def connect(self) -> None:
        """
        Connects the underlying KVStore.
        """
        await self.kv_store.connect()
        await self.kv_store.wait_ready()

    def is_ready(self) -> bool:
        """
        Returns whether the KVStore is ready.
        """
        return self.kv_store.is_ready()

    def _get_key(self, resource_id: str) -> str:
        """
        Builds the Redis key for a lease.
        """
        return f"lease:{resource_id}"

    async def acquire(
        self,
        resource_id: str,
        owner_id: str,
        duration_sec: int,
    ) -> Optional[Lease]:
        """
        Attempts to acquire a lease atomically.

        Uses SET NX + TTL semantics via KVStore.

        Returns:
            Lease if acquired, None if already locked.

        Raises:
            LeaseError on KVStore failure.
        """
        if not self.is_ready():
            raise LeaseError("KVStore is not ready")

        key = self._get_key(resource_id)
        expires_at = datetime.now(timezone.utc).timestamp() + duration_sec

        lease = Lease(
            resource_id=resource_id,
            owner_id=owner_id,
            expires_at=expires_at,
            version=1,
        )

        try:
            acquired = await self.kv_store.set(
                key=key,
                value=lease.to_json(),
                ttl=duration_sec,
                nx=True,
            )
            return lease if acquired else None

        except Exception as exc:
            raise LeaseError(
                f"KVStore error during lease acquisition for '{key}'"
            ) from exc

    async def renew(self, lease: Lease, duration_sec: int) -> bool:
        """
        Renews an existing lease by rewriting its payload and resetting TTL.

        Renewal only succeeds if:
        - the key still exists
        - the owner_id matches
        """
        if not self.is_ready():
            return False

        key = self._get_key(lease.resource_id)

        try:
            raw = await self.kv_store.get(key)
            if raw is None:
                return False

            payload = orjson.loads(raw)
            if isinstance(payload, str):
                payload = orjson.loads(payload)

            if payload.get("owner_id") != lease.owner_id:
                return False

            new_version = payload.get("version", 1) + 1
            new_expires_at = datetime.now(timezone.utc).timestamp() + duration_sec

            renewed = Lease(
                resource_id=lease.resource_id,
                owner_id=lease.owner_id,
                expires_at=new_expires_at,
                version=new_version,
            )

            await self.kv_store.set(
                key=key,
                value=renewed.to_json(),
                ttl=duration_sec,
            )

            lease.version = new_version
            lease.expires_at = new_expires_at

            return True

        except Exception as exc:
            raise LeaseError(f"KVStore error during lease renewal for '{key}'") from exc

    async def release(self, lease: Lease) -> bool:
        """
        Releases a lease by deleting its key.

        Returns:
            True if the lease was released, False otherwise.
        """
        try:
            await self.kv_store.delete(self._get_key(lease.resource_id))
            return True
        except Exception:
            return False
