# src/nala/athomic/database/kvstore/base.py
"""Provides the abstract base class for Key-Value store providers."""

from abc import abstractmethod
from typing import Any, Dict, List, Mapping, Optional

from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.observability.metrics.enums import (
    DbOperation,
    MetricStatus,
)
from nala.athomic.observability.metrics.usage import (
    kvstore_operation_duration_seconds,
    kvstore_operations_total,
)
from nala.athomic.observability.tracing import SpanKind
from nala.athomic.observability.tracing.attributes import (
    DB_KEY,
    DB_OPERATION,
    DB_STATUS,
    DB_SYSTEM,
)
from nala.athomic.services import BaseService

from .protocol import KVStoreProtocol


class BaseKVStore(BaseService, KVStoreProtocol):
    """Abstract base class for all Key-Value Store providers.

    This class provides a template for KV store implementations, handling common
    logic such as service lifecycle, observability (metrics and tracing), and
    serialization. It uses the Template Method pattern, where public methods
    orchestrate the high-level flow and delegate backend-specific operations to
    abstract internal methods (e.g., `_get`, `_set`) that subclasses must
    implement.

    Attributes:
        settings: The configuration for this KV store instance.
        service_name: The unique name for this service instance, used in observability.
        serializer: The serializer instance used for values.
    """

    def __init__(
        self,
        settings: KVStoreSettings,
        service_name: Optional[str] = None,
    ):
        """Initializes the BaseKVStore.

        Args:
            settings: The configuration settings for the provider.
            serializer: An optional serializer instance. If not provided, one
                is created via the `SerializerFactory`.
            service_name: An optional name for the service, used in
                observability.
        """
        self.settings = settings
        self.service_name = service_name or "kvstore"

        super().__init__(service_name=self.service_name, enabled=self.settings.enabled)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves a value from the store by its key.

        This method handles the full get operation, including tracing, metrics,
        and deserialization of the returned value. It delegates the actual
        data fetching to the `_get` method.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The deserialized value, or None if the key is not found.
        """
        operation = DbOperation.GET
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    # serializer module removed for simplicity, as the settings should already handle resolution
                    return await self._get(key)

                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Sets a key-value pair in the store, with an optional TTL.

        This method handles serialization, tracing, and metrics before
        delegating the write operation to the `_set` method.

        Args:
            key: The key of the item to set.
            value: The value to store. It will be serialized.
            ttl: Optional time-to-live for the key in seconds.
            nx: If True, set the key only if it does not already exist.

        Returns:
            True if the operation was successful, False otherwise.
        """
        operation = DbOperation.SET
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    # serialized module removed for simplicity, as the settings should already handle resolution
                    result = await self._set(key, value, ttl, nx)
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        operation = "SET_MANY"
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute("db.keys_count", len(mapping))

                try:
                    if not mapping:
                        return {}

                    # serializer module removed for simplicity, as the settings should already handle resolution

                    result = await self._set_many(mapping, ttl=ttl, nx=nx)

                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.SUCCESS
                    ).inc()
                    return result

                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def delete(self, key: str) -> None:
        """Deletes a key from the store.

        Args:
            key: The key to delete.
        """
        operation = DbOperation.DELETE
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    await self._delete(key)
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def delete_many(self, keys: List[str]) -> int:
        operation = "DELETE_MANY"
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute("db.keys_count", len(keys))

                try:
                    if not keys:
                        return 0

                    count = await self._delete_many(keys)

                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.SUCCESS
                    ).inc()
                    return count

                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def exists(self, key: str) -> bool:
        """Checks if a key exists in the store.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        operation = DbOperation.EXISTS
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._exists(key)
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def clear(self) -> None:
        """Removes all keys from the current database."""
        operation = DbOperation.CLEAR
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                try:
                    await self._clear()
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def is_available(self) -> bool:
        """Checks the availability of the KV service.

        Returns:
            True if the service is connected and ready, False otherwise.
        """
        operation = DbOperation.IS_AVAILABLE
        with self.tracer.start_as_current_span(
            f"KVStore {operation}", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute(DB_SYSTEM, self.service_name)
            try:
                return self.is_ready()
            except Exception as e:
                span.record_exception(e)
                return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increments the integer value of a key by a given amount."""
        operation = "increment"  # Not in DbOperation enum, using string
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._increment(key, amount)
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Adds members with scores to a sorted set.

        Args:
            key: The key of the sorted set.
            mapping: A dictionary of member-score pairs to add.
        """
        operation = DbOperation.ZADD
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    await self._zadd(key, mapping)
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def zrem(self, key: str, members: list[str]) -> int:
        """Removes members from a sorted set.

        Args:
            key: The key of the sorted set.
            members: A list of members to remove.

        Returns:
            The number of members removed.
        """
        operation = DbOperation.ZREM
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._zrem(key, members)
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Atomically retrieves and removes the member with the lowest score.

        Args:
            key: The key of the sorted set.
            max_score: The maximum score of the member to pop.

        Returns:
            The member name, or None if no qualifying members exist.
        """
        operation = DbOperation.ZPOPBYSCORE
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._zpopbyscore(key, max_score)
                    status = MetricStatus.HIT if result else MetricStatus.MISS
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, status
                    ).inc()
                    span.set_attribute(DB_STATUS, status)
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """Retrieves members in a sorted set within a score range.

        Args:
            key: The key of the sorted set.
            min_score: The minimum score of the range.
            max_score: The maximum score of the range.

        Returns:
            A list of member names as bytes.
        """
        operation = DbOperation.ZRANGEBYSCORE
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation.value
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_OPERATION, operation.value)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._zrangebyscore(key, min_score, max_score)
                    status = MetricStatus.HIT if result else MetricStatus.MISS
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, status
                    ).inc()
                    span.set_attribute(DB_STATUS, status)
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation.value, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    # --- Hashes Implementation (NEW) ---

    async def hset(self, key: str, field: str, value: Any) -> int:
        operation = "HSET"
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_KEY, key)
                try:
                    # setializer module removed for simplicity, as the settings should already handle resolution
                    result = await self._hset(key, field, value)
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def hgetall(self, key: str) -> Dict[str, Any]:
        operation = "HGETALL"
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_KEY, key)
                try:
                    raw_dict = await self._hgetall(key)
                    # deserializer module removed for simplicity, as the settings should already handle resolution
                    return raw_dict
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    async def hdel(self, key: str, fields: List[str]) -> int:
        operation = "HDEL"
        with kvstore_operation_duration_seconds.labels(
            self.service_name, operation
        ).time():
            with self.tracer.start_as_current_span(
                f"KVStore {operation}", kind=SpanKind.CLIENT
            ) as span:
                span.set_attribute(DB_SYSTEM, self.service_name)
                span.set_attribute(DB_KEY, key)
                try:
                    result = await self._hdel(key, fields)
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.SUCCESS
                    ).inc()
                    return result
                except Exception as e:
                    kvstore_operations_total.labels(
                        self.service_name, operation, MetricStatus.FAILURE
                    ).inc()
                    span.record_exception(e)
                    raise

    @abstractmethod
    async def _get(self, key: str) -> Optional[bytes]:
        """Fetches the raw value for a key from the backend.

        Subclasses must implement this method to perform the actual data
        retrieval from the specific key-value store.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The raw value as bytes, or None if not found.
        """
        raise NotImplementedError

    @abstractmethod
    async def _set(
        self, key: str, value: bytes, ttl: Optional[int] = None, nx: bool = False
    ) -> bool:
        """Writes the raw value for a key to the backend.

        Subclasses must implement this method to perform the actual write
        operation in the specific key-value store.

        Args:
            key: The key of the item to set.
            value: The serialized value as bytes.
            ttl: Optional time-to-live in seconds.
            nx: If True, set only if the key does not already exist.

        Returns:
            True if the operation was successful.
        """
        raise NotImplementedError

    @abstractmethod
    async def _set_many(
        self,
        mapping: Dict[str, bytes],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """Writes multiple raw values to the backend in a batch."""
        raise NotImplementedError

    @abstractmethod
    async def _delete(self, key: str) -> None:
        """Deletes a key in the backend.

        Args:
            key: The key to delete.
        """
        raise NotImplementedError

    @abstractmethod
    async def _delete_many(self, keys: List[str]) -> int:
        """Deletes multiple keys in the backend in a batch."""
        raise NotImplementedError

    @abstractmethod
    async def _exists(self, key: str) -> bool:
        """Checks for key existence in the backend.

        Args:
            key: The key to check.

        Returns:
            True if the key exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def _clear(self) -> None:
        """Clears all keys in the backend's current database."""
        raise NotImplementedError

    @abstractmethod
    async def _increment(self, key: str, amount: int = 1) -> int:
        """Atomically increments an integer key in the backend.

        Args:
            key: The key to increment.
            amount: The amount to increment by.

        Returns:
            The new value of the key after incrementing.
        """
        raise NotImplementedError

    @abstractmethod
    async def _zadd(self, key: str, mapping: Mapping[str, float]) -> None:
        """Adds members to a sorted set in the backend.

        Args:
            key: The key of the sorted set.
            mapping: A dictionary of member-score pairs.
        """
        raise NotImplementedError

    @abstractmethod
    async def _zrem(self, key: str, members: list[str]) -> int:
        """Removes members from a sorted set in the backend.

        Args:
            key: The key of the sorted set.
            members: A list of members to remove.

        Returns:
            The number of members removed.
        """
        raise NotImplementedError

    @abstractmethod
    async def _zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """Atomically pops a member from a sorted set in the backend.

        Args:
            key: The key of the sorted set.
            max_score: The maximum score of the member to pop.

        Returns:
            The member name, or None if no qualifying member exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def _zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[bytes]:
        """Fetches members by score from a sorted set in the backend.

        Args:
            key: The key of the sorted set.
            min_score: The minimum score of the range.
            max_score: The maximum score of the range.

        Returns:
            A list of member names as bytes.
        """
        raise NotImplementedError

    @abstractmethod
    async def _hset(self, key: str, field: str, value: bytes) -> int:
        raise NotImplementedError

    @abstractmethod
    async def _hgetall(self, key: str) -> Dict[str, bytes]:
        raise NotImplementedError

    @abstractmethod
    async def _hdel(self, key: str, fields: List[str]) -> int:
        raise NotImplementedError
