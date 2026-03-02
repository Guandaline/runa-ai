# src/nala/athomic/config/schemas/performance/cache_config.py
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CacheSettings(BaseModel):
    """Defines the configuration for the caching system.

    This model configures the behavior of the caching layer, including the
    backend storage, serialization, and resilience patterns like fallback caches.

    Attributes:
        enabled (bool): A master switch for the caching system.
        key_prefix (Optional[str]): A global prefix for all generated cache keys.
        kv_store_connection_name (str): The name of the primary KVStore
            connection to use for caching.
        serializer (Optional[SerializerSettings]): The serializer configuration
            for cache data.
        fallback (Optional[FallbackSettings]): Configuration for a fallback
            cache provider.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to enable or disable the caching system globally.",
    )

    key_prefix: Optional[str] = Field(
        default=None,
        alias="KEY_PREFIX",
        description="A global prefix to be added to all generated cache keys, helping to namespace them within the cache store.",
    )

    kv_store_connection_name: str = Field(
        default="default_redis",
        alias="KV_STORE_CONNECTION_NAME",
        description="The name of the primary KVStore connection (defined in `database.kvstore`) to use for caching.",
    )
