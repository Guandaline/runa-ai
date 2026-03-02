from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError

from nala.athomic.config import RedisSettings
from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.database.kvstore.providers.redis import RedisLuaExecutor
from nala.athomic.database.kvstore.providers.redis.client import RedisKVClient

REDIS_ASYNC_CLASS_PATH = "nala.athomic.database.kvstore.providers.redis.client.Redis"
REDIS_SYNC_CLASS_PATH = (
    "nala.athomic.database.kvstore.providers.redis.client.redis.Redis"
)


@pytest.fixture
def kvstore_settings() -> KVStoreSettings:
    """Provides a valid RedisSettings configuration for the tests."""
    return KVStoreSettings(
        enabled=True,
        provider=RedisSettings(uri="redis://mock-host:6379/15", decode_responses=True),
    )


@pytest.fixture
def redis_kv_client(
    kvstore_settings: KVStoreSettings,
) -> RedisKVClient:
    """Instantiates RedisKVClient with the required dependencies."""
    return RedisKVClient(settings=kvstore_settings)


@pytest.fixture
def mock_async_redis_client() -> AsyncMock:
    """
    Provides a mock for the INSTANCE of the redis.asyncio client,
    with its methods also set as async mocks.
    """
    client = AsyncMock(spec=redis.Redis)

    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock()
    client.flushdb = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.aclose = AsyncMock()

    client.zadd = AsyncMock()
    client.zrem = AsyncMock()

    client.hset = AsyncMock()
    client.hgetall = AsyncMock()
    client.hdel = AsyncMock()

    return client


@pytest.fixture
def mock_lua_executor() -> AsyncMock:
    """Provides a mock RedisLuaExecutor."""
    executor = AsyncMock(spec=RedisLuaExecutor)
    executor.execute = AsyncMock()
    return executor


@pytest.mark.asyncio
class TestRedisKVClientLifecycle:
    """Tests focused on lifecycle (connection and closing)."""

    @patch(REDIS_ASYNC_CLASS_PATH)
    async def test_connect_success(
        self, mock_redis_cls: MagicMock, redis_kv_client: RedisKVClient
    ):
        """Checks if _connect creates, starts, and assigns the redis.asyncio client."""
        mock_instance = AsyncMock(spec=redis.Redis)
        mock_instance.ping = AsyncMock(return_value=True)
        mock_redis_cls.return_value = mock_instance

        await redis_kv_client._connect()

        mock_redis_cls.assert_called_once()
        mock_instance.ping.assert_awaited_once()
        assert redis_kv_client._client is mock_instance

    @patch(REDIS_ASYNC_CLASS_PATH)
    async def test_connect_failure(
        self, mock_redis_cls: MagicMock, redis_kv_client: RedisKVClient
    ):
        """Checks if an exception is raised in case of connection failure."""
        mock_redis_cls.side_effect = RedisConnectionError("Connection failed")

        with pytest.raises(RedisConnectionError):
            await redis_kv_client._connect()

        assert redis_kv_client._client is None

    async def test_close_stops_client(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        """Checks if _close calls the client's aclose() method."""
        redis_kv_client._client = mock_async_redis_client

        await redis_kv_client._close()

        mock_async_redis_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
class TestRedisKVClientOperations:
    """Tests focused on data operation methods (_get, _set, etc.)."""

    @pytest.fixture(autouse=True)
    async def setup_mock_client(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        redis_kv_client._client = mock_async_redis_client
        await redis_kv_client.set_ready()
        yield

    async def test_internal_get(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client._get("my-key")
        mock_async_redis_client.get.assert_awaited_once_with("my-key")

    async def test_internal_set(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client._set("my-key", b"my-value", ttl=60, nx=True)
        mock_async_redis_client.set.assert_awaited_once_with(
            "my-key", b"my-value", ex=60, nx=True
        )

    async def test_internal_delete(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client._delete("my-key")
        mock_async_redis_client.delete.assert_awaited_once_with("my-key")

    async def test_internal_exists(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        mock_async_redis_client.exists.return_value = 1
        result = await redis_kv_client._exists("my-key")
        assert result is True

    async def test_internal_clear(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client._clear()
        mock_async_redis_client.flushdb.assert_awaited_once()


class TestSyncClient:
    """Tests the creation of the sync client."""

    @patch(REDIS_SYNC_CLASS_PATH)
    def test_get_sync_client(
        self, mock_sync_redis_cls: MagicMock, redis_kv_client: RedisKVClient
    ):
        sync_client = redis_kv_client.get_sync_client()

        mock_sync_redis_cls.from_url.assert_called_once_with(
            redis_kv_client.settings.uri.get_secret_value(),
            decode_responses=redis_kv_client.settings.decode_responses,
        )
        assert sync_client is mock_sync_redis_cls.from_url.return_value

    def test_get_sync_client_raises_on_missing_uri(
        self, redis_kv_client: RedisKVClient
    ):
        redis_kv_client.settings.uri = None
        with pytest.raises(ValueError):
            redis_kv_client.get_sync_client()


@pytest.mark.asyncio
class TestRedisKVClientSortedSetOperations:
    """Tests for sorted set operations using Lua executor."""

    @pytest.fixture(autouse=True)
    async def setup_mock_client(
        self,
        redis_kv_client: RedisKVClient,
        mock_async_redis_client: AsyncMock,
        mock_lua_executor: AsyncMock,
    ):
        redis_kv_client._client = mock_async_redis_client
        redis_kv_client._lua_executor = mock_lua_executor
        await redis_kv_client.set_ready()
        yield

    async def test_zadd_calls_client_zadd(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client.zadd("my-sorted-set", {"a": 1.0})
        mock_async_redis_client.zadd.assert_awaited_once()

    async def test_zrem_calls_client_zrem(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        await redis_kv_client.zrem("my-sorted-set", ["a", "b"])
        mock_async_redis_client.zrem.assert_awaited_once_with("my-sorted-set", "a", "b")

    async def test_zpopbyscore_loads_and_calls_script(
        self, redis_kv_client: RedisKVClient, mock_lua_executor: AsyncMock
    ):
        mock_lua_executor.execute.return_value = "task-123"

        result = await redis_kv_client.zpopbyscore("my-queue", 12345.67)

        assert result == "task-123"
        mock_lua_executor.execute.assert_awaited_once_with(
            script_name="zpopbyscore",
            keys=["my-queue"],
            args=["12345.67"],
        )

    async def test_zpopbyscore_returns_none_when_script_returns_nil(
        self, redis_kv_client: RedisKVClient, mock_lua_executor: AsyncMock
    ):
        mock_lua_executor.execute.return_value = None

        result = await redis_kv_client.zpopbyscore("my-queue", 12345.67)

        assert result is None


@pytest.mark.asyncio
class TestRedisKVClientHashOperations:
    """Tests for hash-based operations."""

    @pytest.fixture(autouse=True)
    async def setup_mock_client(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        redis_kv_client._client = mock_async_redis_client
        await redis_kv_client.set_ready()
        yield

    async def test_hset_calls_client_hset(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        mock_async_redis_client.hset.return_value = 1
        result = await redis_kv_client._hset("key", "field", b"value")
        assert result == 1

    async def test_hgetall_decodes_keys(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        mock_async_redis_client.hgetall.return_value = {
            b"a": b"1",
            b"b": b"2",
        }

        result = await redis_kv_client._hgetall("key")
        assert result == {"a": b"1", "b": b"2"}

    async def test_hdel_calls_client_hdel(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        mock_async_redis_client.hdel.return_value = 2
        result = await redis_kv_client._hdel("key", ["a", "b"])
        assert result == 2

    async def test_hdel_returns_zero_if_no_fields(
        self, redis_kv_client: RedisKVClient, mock_async_redis_client: AsyncMock
    ):
        result = await redis_kv_client._hdel("key", [])
        assert result == 0
