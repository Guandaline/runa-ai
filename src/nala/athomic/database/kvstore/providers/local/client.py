# src/nala/athomic/database/kvstore/providers/local/client.py
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from nala.athomic.config.schemas.database.kvstore import KVStoreSettings, LocalSettings

from ...base import BaseKVStore

UNSUPPORTED_SORTED_SET_MSG = (
    "Sorted set operations are not supported in the local KV store."
)


class LocalKVClient(BaseKVStore):
    """Simple in-memory implementation of the KVStoreProtocol.

    This provider stores data directly in process memory, supporting optional
    Time-To-Live (TTL) expiration using Python's `datetime` objects. It is ideal
    for unit and integration testing where isolation and speed are critical.

    Attributes:
        _store (Dict[str, Any]): The main dictionary for key-value data storage.
        _expiry (Dict[str, datetime]): Dictionary storing the expiration time for TTL keys.
        _sorted_sets (Dict[str, Dict[str, float]]): Dictionary storing key-score pairs for sorted set simulation.
        _hashes (Dict[str, Dict[str, bytes]]): Dictionary storing field-value pairs for hash simulation.
    """

    # serializer removed for simplicity, as the local provider can directly store Python objects without serialization
    def __init__(
        self,
        settings: KVStoreSettings,
    ):
        """Initializes the LocalKVClient with empty storage and validates settings.

        Args:
            settings (KVStoreSettings): The configuration settings for the provider.
            serializer (Optional[SerializerProtocol]): The serializer instance to use.

        Raises:
            TypeError: If the settings provider is not of type LocalSettings.
        """
        if not isinstance(settings.provider, LocalSettings):
            raise TypeError("LocalKVClient must be initialized with LocalSettings.")

        super().__init__(
            settings=settings,
            service_name="local_kv_provider",
        )

        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
        self._sorted_sets: Dict[str, Dict[str, float]] = {}
        self._hashes: Dict[str, Dict[str, bytes]] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        """Checks if a key has an expiration time set and if it has been exceeded.

        If expired, the key is eagerly removed from both storage and expiration maps.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key is expired, False otherwise.
        """
        exp = self._expiry.get(key)
        if exp and datetime.now(timezone.utc) > exp:
            self._store.pop(key, None)
            self._expiry.pop(key, None)
            return True
        return False

    async def _get(self, key: str) -> Optional[Any]:
        """Fetches a key's value from the in-memory store, checking expiration.

        Args:
            key (str): The key to retrieve.

        Returns:
            Optional[Any]: The stored value, or None if not found or expired.
        """
        if self._is_expired(key):
            return None
        return self._store.get(key)

    async def _set(
        self, key: str, value: bytes, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Writes a key-value pair to the in-memory store.

        Enforces NX (Not Exists) logic and sets the expiration time if a TTL is provided.

        Args:
            key (str): The key to set.
            value (bytes): The serialized value to store.
            ttl (Optional[int]): Time-To-Live in seconds.
            nx (bool): If True, set the key only if it does not already exist.

        Returns:
            bool: False if `nx` is True and the key already exists (and is not expired), True otherwise.
        """
        # Enforce NX rule: return False if key exists and is not expired
        if nx and key in self._store and not self._is_expired(key):
            return False

        self._store[key] = value

        if ttl and ttl > 0:
            # Set absolute expiration time
            self._expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        else:
            # Remove expiration if no TTL is provided
            self._expiry.pop(key, None)

        return True

    async def _set_many(
        self,
        mapping: Dict[str, bytes],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """
        Set multiple key-value pairs in the local key-value store.

        Args:
            mapping (Dict[str, bytes]): Dictionary of key-value pairs to set, where
                keys are strings and values are bytes.
            ttl (Optional[int], optional): Time-to-live in seconds for the keys.
                If None, keys will not expire. Defaults to None.
            nx (bool, optional): If True, only set keys that don't already exist
                (NX - Not eXists). If False, overwrite existing keys. Defaults to False.

        Returns:
            Dict[str, bool]: Dictionary mapping each key to a boolean indicating
                whether the operation was successful. For nx=True, returns False
                if the key already exists, True if successfully set. For nx=False,
                typically returns True for all keys unless an error occurs.

        Note:
            This is a local implementation suitable for testing. Operations are
            performed sequentially in memory.
        """
        results = {}
        # In-memory loop is sufficient for local testing
        for key, value in mapping.items():
            results[key] = await self._set(key, value, ttl=ttl, nx=nx)
        return results

    async def _delete(self, key: str) -> None:
        """Removes a key and its associated expiration record from storage.

        Args:
            key (str): The key to delete.
        """
        self._store.pop(key, None)
        self._expiry.pop(key, None)

    async def _delete_many(self, keys: List[str]) -> int:
        count = 0
        for key in keys:
            # Safely delete even if not exists to mimic standard behavior
            if key in self._store:
                await self._delete(key)
                count += 1
            # Also check expiry map cleanup just in case
            elif key in self._expiry:
                self._expiry.pop(key, None)
        return count

    async def _exists(self, key: str) -> bool:
        """Checks for key existence, handling expiration before returning the result.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists and is not expired, False otherwise.
        """
        if self._is_expired(key):
            return False
        return key in self._store

    async def _clear(self) -> None:
        """Removes all data from the in-memory store.

        Clears key-value pairs, expiration data, sorted sets, and hashes.
        """
        self._store.clear()
        self._expiry.clear()
        self._sorted_sets.clear()
        self._hashes.clear()

    async def _increment(self, key: str, amount: int = 1) -> int:
        """Atomically increments an integer key in the in-memory store.

        Args:
            key (str): The key to increment.
            amount (int): The amount to increment by.

        Returns:
            int: The new value of the key after incrementing.
        """
        async with self._lock:
            if self._is_expired(key):
                raw_value = None
            else:
                raw_value = self._store.get(key)

            try:
                current_value = int(raw_value.decode("utf-8")) if raw_value else 0
            except (ValueError, TypeError):
                current_value = 0

            new_value = current_value + amount
            self._store[key] = str(new_value).encode("utf-8")
            return new_value

    async def _close(self) -> None:
        """Implements the graceful closure.

        No resources to close in in-memory store.
        """
        pass

    async def _connect(self) -> None:
        """Implements the connection.

        No actual connection is needed for in-memory store.
        """
        await self.set_ready()

    async def is_available(self) -> bool:
        """Checks availability.

        Returns:
            bool: Always True, as the in-memory store is considered available once initialized.
        """
        return True

    async def _zadd(self, key: str, mapping: Dict[str, float]) -> None:
        """In-memory implementation of ZADD.

        Adds members to a dictionary simulating a sorted set.

        Args:
            key (str): The key of the sorted set.
            mapping (Dict[str, float]): A dictionary of member-score pairs.
        """
        if key not in self._sorted_sets:
            self._sorted_sets[key] = {}
        # Uses update() to add or overwrite members
        self._sorted_sets[key].update(mapping)

    async def _zrem(self, key: str, members: List[str]) -> int:
        """In-memory implementation of ZREM.

        Removes members from the simulated sorted set.

        Args:
            key (str): The key of the sorted set.
            members (List[str]): A list of members to remove.

        Returns:
            int: The number of members actually removed.
        """
        if key not in self._sorted_sets:
            return 0
        removed_count = 0
        for member in members:
            if self._sorted_sets[key].pop(member, None) is not None:
                removed_count += 1
        return removed_count

    async def _zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """In-memory implementation of ZRANGEBYSCORE.

        Retrieves members within a score range. The result is sorted by score and then
        lexicographically by member name (to emulate Redis behavior).

        Args:
            key (str): The key of the sorted set.
            min_score (float): The minimum score.
            max_score (float): The maximum score.

        Returns:
            List[bytes]: A list of member names encoded as bytes.
        """
        if key not in self._sorted_sets:
            return []

        # Sort by score (item[1]) and then by name (item[0])
        sorted_items = sorted(
            self._sorted_sets[key].items(), key=lambda item: (item[1], item[0])
        )

        result = [
            member.encode("utf-8")
            for member, score in sorted_items
            if min_score <= score <= max_score
        ]
        return result

    async def _zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """In-memory implementation of ZPOPBYSCORE.

        Args:
            key (str): The key of the sorted set.
            max_score (float): The max score.

        Raises:
            NotImplementedError: This complex atomic operation is not fully implemented for the local mock.
        """
        raise NotImplementedError(UNSUPPORTED_SORTED_SET_MSG)

    # --- Hashes Implementation (In-Memory) ---

    async def _hset(self, key: str, field: str, value: bytes) -> int:
        """In-memory implementation of HSET.

        Sets field in the hash stored at key to value.

        Args:
            key (str): The key of the hash.
            field (str): The field name within the hash.
            value (bytes): The value to store.

        Returns:
            int: 1 if field is a new field in the hash and value was set,
                 0 if field already existed in the hash and the value was updated.
        """
        if key not in self._hashes:
            self._hashes[key] = {}

        is_new = field not in self._hashes[key]
        self._hashes[key][field] = value
        return 1 if is_new else 0

    async def _hgetall(self, key: str) -> Dict[str, bytes]:
        """In-memory implementation of HGETALL.

        Returns all fields and values of the hash stored at key.

        Args:
            key (str): The key of the hash.

        Returns:
            Dict[str, bytes]: A dictionary containing all field-value pairs.
                              Returns an empty dict if the key does not exist.
        """
        return self._hashes.get(key, {}).copy()

    async def _hdel(self, key: str, fields: List[str]) -> int:
        """In-memory implementation of HDEL.

        Removes the specified fields from the hash stored at key.

        Args:
            key (str): The key of the hash.
            fields (List[str]): The list of fields to remove.

        Returns:
            int: The number of fields that were removed from the hash,
                 not including specified but non existing fields.
        """
        if key not in self._hashes:
            return 0

        count = 0
        for field in fields:
            if self._hashes[key].pop(field, None) is not None:
                count += 1

        # Cleanup empty hash key to mimic Redis behavior
        if not self._hashes[key]:
            del self._hashes[key]

        return count
