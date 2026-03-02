from typing import Type

from nala.athomic.base import BaseRegistry

from ..protocol import KVStoreProtocol
from .default_ttl_kv_client import DefaultTTLKvClient
from .key_resolver_kv_client import KeyResolvingKVClient


class KVStoreWrapperRegistry(BaseRegistry[Type[KVStoreProtocol]]):
    """Registry for KVStore wrapper classes."""

    def register_defaults(self) -> None:
        """Registers the default schema handlers."""
        self.register("default_ttl", DefaultTTLKvClient)
        self.register("key_resolver", KeyResolvingKVClient)


kv_store_wrapper_registry = KVStoreWrapperRegistry(protocol=KVStoreProtocol)
