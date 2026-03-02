# src/nala/athomic/config/schemas/resilience/rate_limiter/providers/redis_limiter_provider_config.py
from typing import Literal

from pydantic import BaseModel, Field

from nala.athomic.config.schemas.database.kvstore import KVStoreSettings


class RedisLimiterProviderSettings(BaseModel):
    """Configuration settings for the custom Redis Rate Limiter Provider.

    This model defines the necessary settings for the provider that enforces
    rate limits using direct Redis commands, leveraging the application's
    existing KVStore infrastructure.

    Attributes:
        backend (Literal["redis"]): Discriminator field identifying the custom Redis rate limiter provider.
        kvstore (KVStoreSettings): Nested configuration for the KVStore client (which must be a Redis provider) used by the rate limiter for state management and counter persistence.
    """

    # The backend here serves as the discriminator
    backend: Literal["redis"] = Field(
        "redis",
        description="Discriminator field identifying the custom Redis rate limiter provider.",
    )

    # It contains the KVStore configuration that will be used
    kvstore: KVStoreSettings = Field(
        default_factory=KVStoreSettings,
        description="KVStore settings (must be a Redis provider) for the custom rate limiter.",
    )
