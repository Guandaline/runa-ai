# src/nala/athomic/database/kvstore/registry.py
from typing import Type

from nala.athomic.base import BaseRegistry

from .protocol import KVStoreProtocol
from .providers.local.client import LocalKVClient
from .providers.redis.client import RedisKVClient


class KVStoreRegistry(BaseRegistry[Type[KVStoreProtocol]]):
    """Registry for KVStore provider classes."""

    def register_defaults(self) -> None:
        """Registers the default schema handlers."""
        self.register("redis", RedisKVClient)
        self.register("local", LocalKVClient)


kv_store_registry = KVStoreRegistry(protocol=KVStoreProtocol)
