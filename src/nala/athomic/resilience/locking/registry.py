from typing import Type

from nala.athomic.base import BaseRegistry

from .protocol import LockingProtocol
from .providers.local_lock import LocalLockProvider
from .providers.redis_lock import RedisLockProvider


class LockingRegistry(BaseRegistry[Type[LockingProtocol]]):
    """Registry for LockingProtocol implementations."""

    def register_defaults(self) -> None:
        """Registers the default locking providers."""
        self.register("in_memory", LocalLockProvider)
        self.register("redis", RedisLockProvider)


locking_registry = LockingRegistry(protocol=LockingProtocol)
