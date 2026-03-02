# tests/unit/nala/athomic/resilience/locking/test_locking_providers.py
import asyncio
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import LockError

from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.resilience.locking.providers.local_lock import LocalLockProvider
from nala.athomic.resilience.locking.providers.redis_lock import RedisLockProvider

pytestmark = pytest.mark.asyncio

METRICS_PATH = "nala.athomic.resilience.locking.providers"


@mock.patch(f"{METRICS_PATH}.local_lock.locking_hold_duration_seconds")
@mock.patch(f"{METRICS_PATH}.local_lock.locking_attempts_total")
class TestLocalLockProvider:
    """Tests for the in-memory lock provider."""

    async def test_acquire_and_release_successfully(
        self, mock_attempts: MagicMock, mock_duration: MagicMock
    ):
        """Checks if a lock can be acquired and released without contention."""
        # Arrange
        provider = LocalLockProvider()

        # Act
        async with provider.acquire(key="test-key", timeout=1):
            await asyncio.sleep(0.01)  # Simulate work

        # Assert
        mock_attempts.labels.assert_called_once_with(
            lock_name="test-key", backend="in_memory", status="success"
        )
        mock_duration.labels.assert_called_once_with(
            lock_name="test-key", backend="in_memory"
        )

    async def test_timeout_on_contended_lock(
        self, mock_attempts: MagicMock, mock_duration: MagicMock
    ):
        """Checks if the second task fails when trying to acquire a lock already in use."""
        # Arrange
        provider = LocalLockProvider()
        lock_key = "contended-key"

        async def task_that_holds_lock():
            async with provider.acquire(key=lock_key, timeout=1):
                await asyncio.sleep(0.2)

        async def task_that_fails_to_acquire():
            with pytest.raises(asyncio.TimeoutError):
                async with provider.acquire(key=lock_key, timeout=0.1):
                    pytest.fail("This block should not be executed")

        # Act & Assert
        await asyncio.gather(task_that_holds_lock(), task_that_fails_to_acquire())

        assert mock_attempts.labels.call_count == 2
        mock_attempts.labels.assert_any_call(
            lock_name=lock_key, backend="in_memory", status="success"
        )
        mock_attempts.labels.assert_any_call(
            lock_name=lock_key, backend="in_memory", status="failure"
        )

    async def test_different_keys_do_not_block_each_other(
        self, mock_attempts: MagicMock, mock_duration: MagicMock
    ):
        """Checks if locks for different keys do not block each other."""
        # Arrange
        provider = LocalLockProvider()

        task1_acquired = asyncio.Event()
        task2_acquired = asyncio.Event()

        async def task1():
            async with provider.acquire("key1", timeout=1):
                task1_acquired.set()
                await asyncio.sleep(0.1)

        async def task2():
            async with provider.acquire("key2", timeout=1):
                task2_acquired.set()
                await asyncio.sleep(0.1)

        # Act
        await asyncio.gather(task1(), task2())

        # Assert
        assert task1_acquired.is_set()
        assert task2_acquired.is_set()


@mock.patch(f"{METRICS_PATH}.redis_lock.locking_hold_duration_seconds")
@mock.patch(f"{METRICS_PATH}.redis_lock.locking_attempts_total")
class TestRedisLockProvider:
    """Tests for the distributed lock provider with Redis."""

    @pytest.fixture
    def mock_kv_store(self) -> MagicMock:
        """Fixture that creates a complete mock of the KVStore client and Redis client."""
        mock_redis_lock = AsyncMock()
        mock_redis_client = MagicMock()
        mock_redis_client.lock.return_value = mock_redis_lock

        kv_store = MagicMock(spec=KVStoreProtocol)
        kv_store.get_final_client = AsyncMock(return_value=mock_redis_client)

        return kv_store

    async def test_acquire_success(
        self,
        mock_attempts: MagicMock,
        mock_duration: MagicMock,
        mock_kv_store: MagicMock,
    ):
        """Tests the happy path, where the Redis lock is acquired successfully."""
        # Arrange
        provider = RedisLockProvider(kv_store_client=mock_kv_store)

        # Act
        async with provider.acquire(key="redis-key", timeout=10):
            await asyncio.sleep(0.01)  # Simulate work

        # Assert
        mock_kv_store.get_final_client.assert_awaited_once()
        mock_kv_store.get_final_client.return_value.lock.assert_called_once_with(
            name="nalalock:redis-key", timeout=10, blocking_timeout=10
        )
        mock_kv_store.get_final_client.return_value.lock.return_value.__aenter__.assert_awaited_once()
        mock_attempts.labels.assert_called_once_with(
            lock_name="redis-key", backend="redis", status="success"
        )

    async def test_acquire_fails_on_lockerror_raises_timeout(
        self,
        mock_attempts: MagicMock,
        mock_duration: MagicMock,
        mock_kv_store: MagicMock,
    ):
        """Checks if a Redis LockError is converted to asyncio.TimeoutError."""
        # Arrange
        provider = RedisLockProvider(kv_store_client=mock_kv_store)
        mock_kv_store.get_final_client.return_value.lock.return_value.__aenter__.side_effect = LockError(
            "Unable to acquire lock"
        )

        # Act & Assert
        with pytest.raises(asyncio.TimeoutError):
            async with provider.acquire(key="failed-key", timeout=5):
                pytest.fail("This block should not be executed")

        mock_attempts.labels.assert_called_once_with(
            lock_name="failed-key", backend="redis", status="failure"
        )
