from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis
from redis.exceptions import ResponseError

from nala.athomic.database.kvstore.providers.redis import (
    RedisLuaExecutor,
    RedisLuaLoader,
)


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Provides a mocked redis.asyncio client."""
    client = AsyncMock(spec=redis.Redis)
    client.evalsha = AsyncMock()
    client.eval = AsyncMock()
    return client


@pytest.fixture
def mock_lua_loader() -> MagicMock:
    """
    Provides a mocked RedisLuaLoader.

    Contract:
    - load() is async
    - invalidate() is sync
    - get_source() is sync
    """
    loader = MagicMock(spec=RedisLuaLoader)

    loader.load = AsyncMock()
    loader.invalidate = MagicMock()
    loader.get_source = MagicMock()

    return loader


@pytest.fixture
def lua_executor(
    mock_redis_client: AsyncMock, mock_lua_loader: MagicMock
) -> RedisLuaExecutor:
    """Creates a RedisLuaExecutor with mocked dependencies."""
    return RedisLuaExecutor(
        redis_client=mock_redis_client,
        loader=mock_lua_loader,
    )


@pytest.mark.asyncio
class TestRedisLuaExecutor:
    """Tests for RedisLuaExecutor behavior."""

    async def test_execute_uses_evalsha_when_script_is_loaded(
        self,
        lua_executor: RedisLuaExecutor,
        mock_redis_client: AsyncMock,
        mock_lua_loader: MagicMock,
    ):
        """
        Ensures that execute uses EVALSHA when the script SHA is available.
        """
        # Arrange
        mock_lua_loader.load.return_value = "fake-sha"
        mock_redis_client.evalsha.return_value = b"ok"

        # Act
        result = await lua_executor.execute(
            script_name="zpopbyscore",
            keys=["key1"],
            args=["123"],
        )

        # Assert
        assert result == b"ok"

        mock_lua_loader.load.assert_awaited_once_with("zpopbyscore")
        mock_redis_client.evalsha.assert_awaited_once_with(
            "fake-sha",
            1,
            "key1",
            "123",
        )
        mock_redis_client.eval.assert_not_awaited()
        mock_lua_loader.invalidate.assert_not_called()

    async def test_execute_fallbacks_to_eval_on_noscript_error(
        self,
        lua_executor: RedisLuaExecutor,
        mock_redis_client: AsyncMock,
        mock_lua_loader: MagicMock,
    ):
        """
        Ensures that execute falls back to EVAL when Redis reports NOSCRIPT.
        """
        # Arrange
        mock_lua_loader.load.return_value = "stale-sha"
        mock_redis_client.evalsha.side_effect = ResponseError("NOSCRIPT missing")
        mock_lua_loader.get_source.return_value = "return 'ok'"
        mock_redis_client.eval.return_value = b"ok"

        # Act
        result = await lua_executor.execute(
            script_name="zpopbyscore",
            keys=["key1"],
            args=["123"],
        )

        # Assert
        assert result == b"ok"

        mock_lua_loader.invalidate.assert_called_once_with("zpopbyscore")
        mock_lua_loader.get_source.assert_called_once_with("zpopbyscore")
        mock_redis_client.eval.assert_awaited_once_with(
            "return 'ok'",
            1,
            "key1",
            "123",
        )

    async def test_execute_raises_non_noscript_errors(
        self,
        lua_executor: RedisLuaExecutor,
        mock_redis_client: AsyncMock,
        mock_lua_loader: MagicMock,
    ):
        """
        Ensures that Redis errors other than NOSCRIPT are propagated.
        """
        # Arrange
        mock_lua_loader.load.return_value = "fake-sha"
        mock_redis_client.evalsha.side_effect = ResponseError("WRONGTYPE error")

        # Act / Assert
        with pytest.raises(ResponseError):
            await lua_executor.execute(
                script_name="zpopbyscore",
                keys=["key1"],
                args=["123"],
            )

        mock_lua_loader.invalidate.assert_not_called()
        mock_redis_client.eval.assert_not_awaited()
