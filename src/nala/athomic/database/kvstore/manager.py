# src/nala/athomic/database/kvstore/manager.py

from nala.athomic.base.base_manager import BaseManager
from nala.athomic.config.schemas.database.database_config import DatabaseSettings
from nala.athomic.config.schemas.database.kvstore import KVStoreSettings

from .factory import KVStoreFactory
from .protocol import KVStoreProtocol


class KVStoreManager(BaseManager[KVStoreProtocol, KVStoreSettings]):
    """A specialized manager for Key-Value Store connections."""

    def __init__(self, settings: DatabaseSettings):
        super().__init__(
            service_name="kv_store_manager",
            settings=settings.kvstore,
        )
        self.factory = KVStoreFactory
