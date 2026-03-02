# src/nala/athomic/config/schemas/performance/performance_config.py
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .cache_config import CacheSettings


class PerformanceSettings(BaseModel):
    """Defines the top-level configuration for performance-related features.

    This model aggregates settings for various performance optimizations, such as
    caching and response compression, providing a single, organized location for
    tuning the application's performance characteristics.

    Attributes:
        cache (Optional[CacheSettings]): Configuration for the application's
            caching layer.
        compression (Optional[CompressionSettings]): Configuration for the
            HTTP response compression middleware.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    cache: Optional[CacheSettings] = Field(
        default_factory=CacheSettings,
        alias="CACHE",
        description="Configuration for the application's caching layer, including backend storage, TTL, and fallback strategies.",
    )
