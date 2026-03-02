# tests/unit/nala/athomic/resilience/circuit_breaker/test_cb_storage_factory.py
import asyncio
from unittest.mock import MagicMock, patch

import pytest
from aiobreaker.storage.memory import CircuitMemoryStorage

from nala.athomic.config.schemas import (
    CircuitBreakerSettings,
    LocalCircuitBreakerStorageSettings,
    RedisCircuitBreakerStorageSettings,
    RedisSettings,
)
from nala.athomic.resilience.circuit_breaker.patched_storage import (
    PatchedCircuitRedisStorage,
)
from nala.athomic.resilience.circuit_breaker.storage_factory import (
    CircuitBreakerStorageFactory,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis_setup():
    with patch(
        "nala.athomic.resilience.circuit_breaker.storage_factory.sync_redis.from_url"
    ) as mock_from_url_func:
        mock_returned_redis_client = MagicMock()
        mock_returned_redis_client.ping.return_value = True
        mock_from_url_func.return_value = mock_returned_redis_client
        yield mock_from_url_func, mock_returned_redis_client


async def test_create_redis_storage_success(mock_redis_setup):
    mock_from_url, mock_redis_client = mock_redis_setup
    settings = CircuitBreakerSettings(
        namespace="test_ns",
        provider=RedisCircuitBreakerStorageSettings(
            redis=RedisSettings(uri="redis://test")
        ),
    )

    storage = await CircuitBreakerStorageFactory.create(
        circuit_name="my_circuit", settings=settings
    )

    assert isinstance(storage, PatchedCircuitRedisStorage)
    mock_from_url.assert_called_once_with("redis://test")
    with patch("asyncio.to_thread"):
        await asyncio.to_thread(mock_redis_client.ping)


async def test_create_redis_storage_fallback_on_connection_error(mock_redis_setup):
    _mock_from_url, mock_redis_client = mock_redis_setup
    mock_redis_client.ping.side_effect = ConnectionError("Redis is down")
    settings = CircuitBreakerSettings(
        provider=RedisCircuitBreakerStorageSettings(
            redis=RedisSettings(uri="redis://test")
        )
    )

    storage = await CircuitBreakerStorageFactory.create(
        circuit_name="my_circuit", settings=settings
    )

    assert isinstance(storage, CircuitMemoryStorage)


async def test_create_memory_storage():
    settings = CircuitBreakerSettings(provider=LocalCircuitBreakerStorageSettings())

    storage = await CircuitBreakerStorageFactory.create(
        circuit_name="my_circuit", settings=settings
    )

    assert isinstance(storage, CircuitMemoryStorage)
