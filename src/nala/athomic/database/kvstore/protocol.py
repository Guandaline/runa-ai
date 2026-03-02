# src/nala/athomic/database/kvstore/protocol.py
"""Defines the abstract interface (Protocol) for Key-Value store providers."""

from typing import Any, Dict, List, Mapping, Optional, Protocol, runtime_checkable

from nala.athomic.services.protocol import BaseServiceProtocol


@runtime_checkable
class KVStoreProtocol(BaseServiceProtocol, Protocol):
    """Defines the contract for an asynchronous Key-Value store provider.

    This protocol specifies the standard interface for all key-value store
    implementations within the framework. It includes basic CRUD operations,
    sorted set commands, and lifecycle management. Any class that conforms to
    this protocol can be used as a KV store backend for features like caching,
    batch operate, rate limiting, and feature flags.
    """

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves a value by its key.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The deserialized value, or None if the key is not found.
        """
        ...

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Sets a key-value pair, with an optional TTL.

        Args:
            key: The key of the item to set.
            value: The value to store. It will be serialized by the provider.
            ttl: Optional time-to-live for the key in seconds.
            nx: If True, set the key only if it does not already exist.

        Returns:
            True if the operation was successful.
        """
        ...

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """Sets multiple key-value pairs in a single operation.

        Args:
            mapping: A dictionary of key-value pairs to store.
            ttl: Optional TTL in seconds applied to all keys in this batch.
            nx: If True, only sets keys that do not exist (atomic per key).

        Returns:
            A dictionary mapping each key to a boolean indicating success.
        """
        ...

    async def delete(self, key: str) -> None:
        """Deletes a key from the store.

        Args:
            key: The key to delete.
        """
        ...

    async def delete_many(self, keys: List[str]) -> int:
        """Deletes multiple keys in a single operation.

        Args:
            keys: A list of keys to delete.

        Returns:
            The number of keys actually deleted.
        """
        ...

    async def exists(self, key: str) -> bool:
        """Checks if a key exists in the store.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        ...

    async def clear(self) -> None:
        """Removes all keys from the current database."""
        ...

    async def is_available(self) -> bool:
        """Checks if the provider is connected and ready to accept operations.

        Returns:
            True if the service is ready, False otherwise.
        """
        ...

    async def connect(self) -> None:
        """Establishes the connection to the backend service."""
        ...

    async def close(self) -> None:
        """Closes the connection to the backend service."""
        ...

    async def zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Adds one or more members with scores to a sorted set.

        Args:
            key: The key of the sorted set.
            mapping: A dictionary of member-score pairs to add.
        """
        ...

    async def zrem(self, key: str, members: list[str]) -> int:
        """Removes one or more members from a sorted set.

        Args:
            key: The key of the sorted set.
            members: A list of members to remove.

        Returns:
            The number of members that were removed from the set.
        """
        ...

    async def zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Atomically removes and returns the member with the lowest score.

        The member returned is the one with the lowest score that is less than
        or equal to the `max_score`.

        Args:
            key: The key of the sorted set.
            max_score: The maximum score to consider for popping a member.

        Returns:
            The member name as a string, or None if no qualifying members exist.
        """
        ...

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> list[str]:
        """Returns members of a sorted set within a score range.

        Retrieves all members in a sorted set with scores between `min_score`
        and `max_score` (inclusive).

        Args:
            key: The key of the sorted set.
            min_score: The minimum score of the range.
            max_score: The maximum score of the range.

        Returns:
            A list of member names.
        """
        ...

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increments the integer value of a key by a given amount.

        If the key does not exist, it is set to 0 before performing the operation.

        Args:
            key: The key of the item to increment.
            amount: The amount to increment by. Defaults to 1.

        Returns:
            The value of the key after the increment.
        """
        ...

    # --- Hashes ---
    async def hset(self, key: str, field: str, value: Any) -> int:
        """Sets field in the hash stored at key to value."""
        ...

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Returns all fields and values of the hash stored at key."""
        ...

    async def hdel(self, key: str, fields: List[str]) -> int:
        """Removes the specified fields from the hash stored at key."""
        ...

    async def get_final_client(self) -> Any:
        """Returns the underlying raw asynchronous client instance.

        This provides an escape hatch to access provider-specific features
        not covered by the protocol (e.g., calling a unique Redis command).

        Returns:
            The raw provider-specific async client instance (e.g., `redis.asyncio.Redis`).
        """
        ...

    def get_sync_client(self) -> Any:
        """Returns an underlying raw synchronous client instance, if applicable.

        Returns:
            The raw provider-specific sync client instance (e.g., `redis.Redis`).

        Raises:
            NotImplementedError: If a synchronous client is not available or
                supported by the provider.
        """
        raise NotImplementedError("Synchronous client not available for this provider.")
