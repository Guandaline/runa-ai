from typing import Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.asyncio.connection import parse_url as async_parse_url

from nala.athomic.config import RedisSettings
from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.config.settings import get_settings
from nala.athomic.observability.log import get_logger
from nala.athomic.services.exceptions import ServiceNotReadyError

from ...base import BaseKVStore
from .lua import RedisLuaExecutor, RedisLuaLoader

logger = get_logger(__name__)

REDIS_CLIENT_NOT_CONNECTED_MSG = "Redis client is not connected."


class RedisKVClient(BaseKVStore):
    """
    A concrete KVStoreProvider implementation for Redis using the aioredis library.
    """

    def __init__(
        self,
        settings: Optional[KVStoreSettings] = None,
    ):
        """
        Initializes the RedisKVClient.
        """
        if not settings:
            settings = get_settings().database.kvstore

        namespace = settings.namespace or "default"

        super().__init__(
            settings=settings,
            service_name=f"redis_kv_{namespace}",
        )

        self.settings: RedisSettings = settings.provider
        self._client: Redis | None = None
        self._sync_client: Optional[redis.Redis] = None

        self._lua_loader: Optional[RedisLuaLoader] = None
        self._lua_executor: Optional[RedisLuaExecutor] = None

    async def _get_connection_uri(self) -> str:
        """
        Determines the Redis connection URI, resolving credentials from settings.
        """
        uri = self.settings.uri
        if hasattr(uri, "get_secret_value"):
            return uri.get_secret_value()
        return str(uri)

    async def _connect(self) -> None:
        """
        Initializes and connects the asynchronous Redis client.
        """
        connection_uri = await self._get_connection_uri()
        self.logger.info("Connecting to Redis...")
        self.logger.debug("Using Redis connection URI")

        connection_kwargs = async_parse_url(connection_uri)

        self._client = Redis(
            **connection_kwargs,
            decode_responses=self.settings.decode_responses,
            socket_connect_timeout=self.settings.socket_connect_timeout or 5,
        )

        await self._client.ping()
        self.logger.success("Redis client connected and PING OK.")

        self._lua_loader = RedisLuaLoader(self._client)
        self._lua_executor = RedisLuaExecutor(
            redis_client=self._client,
            loader=self._lua_loader,
        )

        await self.set_ready()

    async def _close(self) -> None:
        """
        Closes the asynchronous Redis client connection.
        """
        if self._client:
            await self._client.aclose()
            self.logger.info("Redis client connection closed.")

    async def _get(self, key: str) -> Optional[Union[bytes, str]]:
        """
        Fetches the raw value for a key from the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        return await self._client.get(key)

    async def _set(
        self,
        key: str,
        value: Union[bytes, str],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        """
        Writes the raw value for a key to the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        return await self._client.set(key, value, ex=ttl, nx=nx)

    async def _set_many(
        self,
        mapping: Dict[str, Union[bytes, str]],
        ttl: Optional[int] = None,
        nx: bool = False,
    ) -> Dict[str, bool]:
        """
        Set multiple key-value pairs in Redis with optional TTL and existence conditions.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)

        if not mapping:
            return {}

        async with self._client.pipeline() as pipe:
            keys_order = list(mapping.keys())

            for key in keys_order:
                pipe.set(key, mapping[key], ex=ttl, nx=nx)

            results = await pipe.execute()

        return dict(zip(keys_order, [bool(r) for r in results]))

    async def _delete(self, key: str) -> None:
        """
        Deletes a key in the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        await self._client.delete(key)

    async def _delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys from the Redis store.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)

        if not keys:
            return 0

        return await self._client.delete(*keys)

    async def _exists(self, key: str) -> bool:
        """
        Checks for key existence in the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        result = await self._client.exists(key)
        return result > 0

    async def _clear(self) -> None:
        """
        Removes all keys from the current Redis database.
        """
        if not self.is_ready() or not self._client:
            raise ServiceNotReadyError(
                f"Service '{self.service_name}' is not connected or ready."
            )
        await self._client.flushdb()

    async def _increment(self, key: str, amount: int = 1) -> int:
        """
        Atomically increments an integer key in the backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        return await self._client.incrby(key, amount)

    async def _zadd(self, key: str, mapping: dict[str, float]) -> None:
        """
        Adds members with scores to a sorted set in the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        await self._client.zadd(key, mapping)

    async def _zrem(self, key: str, members: list[str]) -> int:
        """
        Removes members from a sorted set in the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        return await self._client.zrem(key, *members)

    async def _zpopbyscore(self, key: str, max_score: float) -> Optional[str]:
        """
        Atomically pops a member from a sorted set using a preloaded Lua script.
        """
        if not self.is_ready() or not self._client or not self._lua_executor:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)

        return await self._lua_executor.execute(
            script_name="zpopbyscore",
            keys=[key],
            args=[str(max_score)],
        )

    async def _zrangebyscore(
        self, key: str, min_score: float, max_score: float
    ) -> List[Union[bytes, str]]:
        """
        Fetches members by score from a sorted set in the Redis backend.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)

        return await self._client.zrangebyscore(key, min_score, max_score)

    async def get_final_client(self) -> Redis:
        """
        Returns the raw asynchronous Redis client instance.
        """
        if not self.is_ready() or not self._client:
            raise ServiceNotReadyError(
                f"Service '{self.service_name}' is not connected or ready."
            )
        return self._client

    def get_sync_client(self) -> redis.Redis:
        """
        Creates and returns a NEW instance of the synchronous Redis client.
        """
        if not self.settings.uri:
            raise ValueError("Redis URI is not available to create a sync client.")

        uri = self.settings.uri
        uri_str = (
            uri.get_secret_value() if hasattr(uri, "get_secret_value") else str(uri)
        )

        self.logger.debug("Creating NEW SYNCHRONOUS Redis client for URI")
        try:
            if self._sync_client is None:
                self._sync_client = redis.Redis.from_url(
                    uri_str,
                    decode_responses=self.settings.decode_responses,
                )

            return self._sync_client
        except Exception as e:
            self.logger.exception("Failed to create synchronous Redis client.")
            raise RuntimeError(f"Could not create sync Redis client: {e}") from e

    async def _hset(self, key: str, field: str, value: Union[bytes, str]) -> int:
        """
        Sets a field in a hash to a value.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        return await self._client.hset(key, field, value)

    async def _hgetall(self, key: str) -> dict[str, Union[bytes, str]]:
        """
        Gets all the fields and values in a hash.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)

        raw = await self._client.hgetall(key)

        return {
            k.decode("utf-8") if isinstance(k, bytes) else k: v for k, v in raw.items()
        }

    async def _hdel(self, key: str, fields: List[str]) -> int:
        """
        Deletes one or more hash fields.
        """
        if not self.is_ready() or not self._client:
            raise RuntimeError(REDIS_CLIENT_NOT_CONNECTED_MSG)
        if not fields:
            return 0
        return await self._client.hdel(key, *fields)
