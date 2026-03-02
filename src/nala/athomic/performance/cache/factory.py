# /src/nala/athomic/performance/cache/factory.py
from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.performance.cache_config import CacheSettings
from nala.athomic.database.factory import connection_manager_factory
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.database.manager import ConnectionManager
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class CacheFallbackFactory:
    """
    A Factory responsible for creating and configuring the final KVStoreProtocol
    instance for caching, which may be a simple primary client or a resilient
    """

    @classmethod
    def create(
        cls,
        settings: Optional[CacheSettings] = None,
        connection_manager: Optional[ConnectionManager] = None,
    ) -> KVStoreProtocol:
        """
        Assembles the cache providers based on settings.

        Args:
            settings: Optional explicit settings to override global configuration.
            connection_manager: Optional ConnectionManager instance for dependency injection.

        Raises:
            ValueError: If caching is disabled in the configuration.

        Returns:
            KVStoreProtocol: The fully configured KVStore client (primary or fallback chain).
        """
        settings: CacheSettings = settings or get_settings().performance.cache

        # 1. Validation (Circuit Breaker)
        if not settings.enabled:
            raise ValueError("Cache is disabled in the configuration.")

        # 2. Resolve ConnectionManager (use injected or create via factory)
        resolved_cm = connection_manager or connection_manager_factory.create()

        # 3. Resolve Primary Client
        primary_connection_name = settings.kv_store_connection_name
        logger.debug(f"Requesting primary cache provider: '{primary_connection_name}'")

        # Get the primary client from the global connection pool
        primary_client = resolved_cm.get_kv_store(primary_connection_name)

        logger.info("No fallback cache configured. Using primary provider only.")
        return primary_client
