from redis import Redis
from redis.exceptions import ResponseError

from .lua_loader import RedisLuaLoader


class RedisLuaExecutor:
    """
    Executes Redis Lua scripts via EVALSHA with safe fallback to EVAL.
    """

    def __init__(self, redis_client: Redis, loader: RedisLuaLoader):
        self._redis: Redis = redis_client
        self._loader: RedisLuaLoader = loader

    async def execute(
        self,
        script_name: str,
        keys: list[str],
        args: list[str],
    ):
        sha = await self._loader.load(script_name)

        try:
            return await self._redis.evalsha(
                sha,
                len(keys),
                *keys,
                *args,
            )
        except ResponseError as exc:
            if "NOSCRIPT" not in str(exc):
                raise

            self._loader.invalidate(script_name)
            source = self._loader.get_source(script_name)

            return await self._redis.eval(
                source,
                len(keys),
                *keys,
                *args,
            )
