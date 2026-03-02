# src/nala/athomic/resilience/locking/providers/redis_lock.py
import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.exceptions import LockError

from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.observability.decorators import with_observability
from nala.athomic.observability.log import get_logger
from nala.athomic.observability.metrics import MetricStatus
from nala.athomic.observability.metrics.usage.locking_metrics import (
    locking_attempts_total,
    locking_hold_duration_seconds,
)

from ..protocol import LockingProtocol

logger = get_logger(__name__)


class RedisLockProvider(LockingProtocol):
    """
    A distributed locking provider implementation using Redis (via the underlying
    `redis.asyncio` client) and its atomic locking primitives.

    It integrates seamlessly with the application's `KVStoreProtocol` to obtain
    the necessary Redis connection.
    """

    def __init__(self, kv_store_client: KVStoreProtocol):
        """
        Initializes the RedisLockProvider.

        Args:
            kv_store_client (KVStoreProtocol): The configured KV store client
                                               from which to retrieve the raw Redis connection.
        """
        self.kv_store = kv_store_client
        # The raw redis client is resolved lazily on the first `acquire` call
        self._redis_client = None

    @asynccontextmanager
    @with_observability(
        name="locking.provider.redis.acquire", attributes_from_args={"key": "lock.key"}
    )
    async def acquire(self, key: str, timeout: int = 30) -> AsyncGenerator[None, None]:
        """
        Acquires a distributed lock for a specific key.

        This method leverages the `redis.asyncio.lock` object, ensuring thread-safe
        acquisition with a defined timeout. Metrics are recorded for both successful
        attempts and acquisition failures.

        Args:
            key (str): The logical key of the resource to lock.
            timeout (int): The maximum time (in seconds) to wait to acquire the lock.
                           Also sets the lock's expiration time.

        Yields:
            None: Execution context for the protected operation.

        Raises:
            asyncio.TimeoutError: If the lock cannot be acquired within the timeout.
        """
        # Resolve the raw Redis client lazily
        if not self._redis_client:
            self._redis_client = await self.kv_store.get_final_client()

        # Construct a unique, namespaced key for the Redis lock mechanism
        lock_key = f"nalalock:{key}"

        # Create a lock instance. `blocking_timeout` controls how long we wait to acquire it.
        lock_instance = self._redis_client.lock(
            name=lock_key, timeout=timeout, blocking_timeout=timeout
        )

        start_time = time.monotonic()
        status = MetricStatus.FAILURE

        try:
            # Attempt to acquire the lock using the async context manager
            async with lock_instance:
                status = MetricStatus.SUCCESS
                logger.info(f"Distributed lock acquired: {lock_key}")
                yield
        except LockError as e:
            # `LockError` is raised by the underlying redis-py client on acquisition failure/timeout
            logger.error(f"Failed to acquire distributed lock for key '{key}': {e}")
            # Map the `LockError` to the standard `asyncio.TimeoutError` expected by the LockingProtocol
            raise asyncio.TimeoutError(f"Could not acquire lock for {key}") from e
        finally:
            duration = time.monotonic() - start_time

            # Record total attempt count and status
            locking_attempts_total.labels(
                lock_name=key, backend="redis", status=status
            ).inc()

            # Record duration only for successfully acquired locks
            if status == MetricStatus.SUCCESS:
                locking_hold_duration_seconds.labels(
                    lock_name=key, backend="redis"
                ).observe(duration)

            logger.debug(f"Distributed lock released: {lock_key}")
