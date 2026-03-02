# nala/athomic/performance/cache/protocol.py
from nala.athomic.context.types import ContextualKeyResolverType
from nala.athomic.database.kvstore.protocol import KVStoreProtocol as CacheProtocol

__all__ = ["CacheProtocol", "ContextualKeyResolverType"]
