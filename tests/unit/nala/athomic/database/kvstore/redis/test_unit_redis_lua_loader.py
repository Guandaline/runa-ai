from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from nala.athomic.database.kvstore.providers.redis import (
    RedisLuaLoader,
    redis_lua_script_registry,
)


@pytest.fixture
def redis_client():
    return AsyncMock()


@pytest.fixture
def lua_loader(redis_client):
    return RedisLuaLoader(redis_client=redis_client)


@pytest.fixture
def temp_lua_script(tmp_path: Path):
    """
    Creates a temporary Lua script file and registers it
    in the redis_lua_script_registry for the duration of the test.

    IMPORTANT:
    - InstanceRegistry.get() raises ValueError if missing
    - Therefore we must NOT call get() before register()
    - UUID guarantees uniqueness, so safe to remove blindly
    """
    script_name = f"test_lua_script_{uuid4().hex}"
    script_path = tmp_path / f"{script_name}.lua"
    script_path.write_text("return 1", encoding="utf-8")

    redis_lua_script_registry.register(script_name, script_path)

    try:
        yield script_name
    finally:
        # Test-only cleanup: registry is global
        redis_lua_script_registry._registry.pop(script_name, None)


class TestRedisLuaLoader:
    async def test_load_reads_script_and_caches_sha(
        self,
        lua_loader: RedisLuaLoader,
        redis_client: AsyncMock,
        temp_lua_script: str,
    ):
        redis_client.script_load.return_value = "sha-123"

        sha = await lua_loader.load(temp_lua_script)

        assert sha == "sha-123"
        redis_client.script_load.assert_awaited_once()
        assert lua_loader._sha_cache[temp_lua_script] == "sha-123"

    async def test_load_uses_cached_sha_when_available(
        self,
        lua_loader: RedisLuaLoader,
        redis_client: AsyncMock,
        temp_lua_script: str,
    ):
        lua_loader._sha_cache[temp_lua_script] = "cached-sha"

        sha = await lua_loader.load(temp_lua_script)

        assert sha == "cached-sha"
        redis_client.script_load.assert_not_awaited()

    def test_get_source_reads_script_from_registry(
        self,
        lua_loader: RedisLuaLoader,
        temp_lua_script: str,
    ):
        source = lua_loader.get_source(temp_lua_script)

        assert source.strip() == "return 1"

    def test_invalidate_removes_cached_sha(
        self,
        lua_loader: RedisLuaLoader,
        temp_lua_script: str,
    ):
        lua_loader._sha_cache[temp_lua_script] = "to-be-removed"

        lua_loader.invalidate(temp_lua_script)

        assert temp_lua_script not in lua_loader._sha_cache

    def test_invalidate_is_idempotent(
        self,
        lua_loader: RedisLuaLoader,
        temp_lua_script: str,
    ):
        lua_loader.invalidate(temp_lua_script)
        lua_loader.invalidate(temp_lua_script)

        assert temp_lua_script not in lua_loader._sha_cache
