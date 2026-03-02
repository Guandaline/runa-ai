from typing import Dict

from .registry import (
    redis_lua_script_registry,
)


class RedisLuaLoader:
    """
    Loads Redis Lua scripts using SCRIPT LOAD and caches SHAs.
    """

    def __init__(self, redis_client):
        self._redis = redis_client
        self._sha_cache: Dict[str, str] = {}

    async def load(self, script_name: str) -> str:
        if script_name in self._sha_cache:
            return self._sha_cache[script_name]

        source = self.get_source(script_name)
        sha = await self._redis.script_load(source)
        self._sha_cache[script_name] = sha
        return sha

    def get_source(self, script_name: str) -> str:
        path = redis_lua_script_registry.get(script_name)
        return path.read_text(encoding="utf-8")

    def invalidate(self, script_name: str) -> None:
        self._sha_cache.pop(script_name, None)
