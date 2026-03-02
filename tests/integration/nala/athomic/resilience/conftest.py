import asyncio
from unittest.mock import AsyncMock

import pytest

from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.config.schemas.database.kvstore.providers.local_config import (
    LocalSettings,
)
from nala.athomic.config.schemas.database.kvstore.providers.redis_config import (
    RedisSettings,
)
from nala.athomic.database.kvstore.exceptions import KVStoreError
from nala.athomic.database.kvstore.providers import LocalKVClient, RedisKVClient

TEST_REDIS_URL = "redis://localhost:6379/14"


@pytest.fixture(scope="function")
async def redis_kv_client():
    settings = KVStoreSettings(
        provider=RedisSettings(
            uri=TEST_REDIS_URL, namespace="test_namespace", enabled=True
        )
    )
    client = RedisKVClient(settings=settings)
    await client.connect()

    yield client

    await client.clear()
    await client.close()


@pytest.fixture(scope="function")
def in_memory_kv_client():
    settings = KVStoreSettings(provider=LocalSettings(type="local", enabled=True))
    return LocalKVClient(settings=settings)


@pytest.fixture
def failing_kv_provider():
    ERROR_MSG = "Provider is intentionally failing"
    mock = AsyncMock()
    mock.get.side_effect = KVStoreError(ERROR_MSG)
    mock.exists.side_effect = KVStoreError(ERROR_MSG)
    mock.set.side_effect = KVStoreError(ERROR_MSG)
    return mock


@pytest.fixture
def slow_kv_provider():
    mock = AsyncMock()

    async def slow_get(key: str):
        await asyncio.sleep(5)
        return "slow_value"

    mock.get.side_effect = slow_get
    return mock
