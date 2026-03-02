# tests/unit/nala/athomic/resilience/locking/test_locking_factory.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import LockError

from nala.athomic.config import LockingSettings
from nala.athomic.config.schemas.database import (
    KVStoreSettings,
)
from nala.athomic.config.schemas.resilience.locking_config import (
    InMemoryLockProviderSettings,
    RedisLockProviderSettings,
)
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.resilience.locking.factory import LockingFactory
from nala.athomic.resilience.locking.providers.local_lock import (
    LocalLockProvider,
)
from nala.athomic.resilience.locking.providers.redis_lock import RedisLockProvider
from nala.athomic.resilience.locking.registry import locking_registry

GET_SETTINGS_PATH = "nala.athomic.resilience.locking.factory.get_settings"
KV_FACTORY_CREATE_PATH = "nala.athomic.resilience.locking.factory.KVStoreFactory.create"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Clears the factory cache and registry before and after each test."""

    locking_registry.clear()
    locking_registry.register(name="redis", item_class=RedisLockProvider)
    locking_registry.register(name="in_memory", item_class=LocalLockProvider)
    LockingFactory.clear_cache()
    yield
    LockingFactory.clear_cache()
    locking_registry.clear()


@pytest.fixture
def mock_kv_store() -> MagicMock:
    """Fixture that creates a mock for KVStoreProtocol."""
    kv_store = MagicMock(spec=KVStoreProtocol)
    kv_store.get_final_client = AsyncMock()
    return kv_store


@patch(KV_FACTORY_CREATE_PATH)
@patch(GET_SETTINGS_PATH)
def test_factory_creates_redis_provider(
    mock_get_settings: MagicMock,
    mock_kv_factory_create: MagicMock,
    mock_kv_store: MagicMock,
):
    """
    Tests if the factory creates a RedisLockProvider when the configuration specifies 'redis'.
    """
    # Arrange
    mock_kv_factory_create.return_value = mock_kv_store

    valid_kv_settings = KVStoreSettings()
    redis_provider_settings = RedisLockProviderSettings(kvstore=valid_kv_settings)

    mock_locking_settings = LockingSettings(provider=redis_provider_settings)
    mock_get_settings.return_value.resilience.locking = mock_locking_settings

    # Act
    provider = LockingFactory.create()

    # Assert
    assert isinstance(provider, RedisLockProvider)
    mock_kv_factory_create.assert_called_once_with(settings=valid_kv_settings)
    assert provider.kv_store is mock_kv_store


@patch(GET_SETTINGS_PATH)
def test_factory_creates_in_memory_provider(mock_get_settings: MagicMock):
    """
    Tests if the factory creates an InMemoryLockProvider when the configuration specifies 'in_memory'.
    """
    in_memory_provider_settings = InMemoryLockProviderSettings()
    mock_locking_settings = LockingSettings(provider=in_memory_provider_settings)
    mock_get_settings.return_value.resilience.locking = mock_locking_settings

    provider = LockingFactory.create()
    assert isinstance(provider, LocalLockProvider)


@patch(GET_SETTINGS_PATH)
def test_factory_creates_in_memory_provider_when_disabled(mock_get_settings: MagicMock):
    """
    Tests if the factory creates an InMemoryLockProvider as a fallback if locking is disabled.
    """
    mock_locking_settings = LockingSettings(enabled=False)
    mock_get_settings.return_value.resilience.locking = mock_locking_settings

    provider = LockingFactory.create()
    assert isinstance(provider, LocalLockProvider)


@pytest.mark.asyncio
async def test_redis_provider_acquire_lock_success(mock_lock_object: AsyncMock):
    """Tests the success flow of acquire in RedisLockProvider."""
    # Arrange
    mock_redis_client = AsyncMock()
    mock_redis_client.lock = MagicMock(return_value=mock_lock_object)

    mock_kv_store = AsyncMock(spec=KVStoreProtocol)
    mock_kv_store.get_final_client.return_value = mock_redis_client

    provider = RedisLockProvider(kv_store_client=mock_kv_store)
    operation_executed = False

    # Act
    async with provider.acquire("my-redis-key", timeout=30):
        operation_executed = True

    # Assert
    assert operation_executed is True
    mock_kv_store.get_final_client.assert_awaited_once()
    mock_redis_client.lock.assert_called_once_with(
        name="nalalock:my-redis-key", timeout=30, blocking_timeout=30
    )
    mock_lock_object.__aenter__.assert_awaited_once()
    mock_lock_object.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_provider_acquire_lock_fails(mock_lock_object: AsyncMock):
    """Tests failure to acquire lock in RedisLockProvider."""
    # Arrange
    mock_redis_client = AsyncMock()
    mock_redis_client.lock = MagicMock(return_value=mock_lock_object)
    mock_lock_object.__aenter__.side_effect = LockError("Could not acquire lock")

    mock_kv_store = AsyncMock(spec=KVStoreProtocol)
    mock_kv_store.get_final_client.return_value = mock_redis_client

    provider = RedisLockProvider(kv_store_client=mock_kv_store)

    # Act & Assert
    with pytest.raises(
        asyncio.TimeoutError, match="Could not acquire lock for my-failing-key"
    ):
        async with provider.acquire("my-failing-key"):
            pytest.fail("Code inside 'with' should not have been executed.")

    mock_lock_object.__aenter__.assert_awaited_once()
    mock_lock_object.__aexit__.assert_not_awaited()


@pytest.mark.asyncio
async def test_in_memory_provider_acquire_lock_success():
    """Tests the success flow of InMemoryLockProvider."""
    provider = LocalLockProvider()
    operation_executed = False

    # Act
    async with provider.acquire("my-in-memory-key", timeout=1):
        operation_executed = True

    # Assert
    assert operation_executed is True
