# src/nala/athomic/config/schemas/resilience/circuit_breaker/circuit_breaker_storage_config.py
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...database.kvstore.providers.redis_config import RedisSettings


class LocalCircuitBreakerStorageSettings(BaseModel):
    """Defines the configuration for in-memory circuit breaker state storage.

    This model selects the in-memory storage backend, suitable for local
    development and single-instance deployments. The state is not persistent
    and is not shared across multiple service instances.

    Attributes:
        backend (Literal["local"]): The discriminator field that identifies
            this as the local in-memory storage provider.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["local"] = Field(
        default="local",
        description="The discriminator field that identifies this as the local in-memory storage provider.",
    )


class RedisCircuitBreakerStorageSettings(BaseModel):
    """Defines the configuration for Redis-based circuit breaker state storage.

    This model selects Redis as the distributed storage backend for circuit
    breaker states. This is the recommended option for multi-instance deployments,
    as it allows all service instances to share the same circuit state.

    Attributes:
        backend (Literal["redis"]): The discriminator field that identifies
            this as the Redis storage provider.
        redis (RedisSettings): The settings for the Redis connection used by
            the circuit breaker storage.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["redis"] = Field(
        default="redis",
        description="The discriminator field that identifies this as the Redis storage provider.",
    )

    redis: RedisSettings = Field(
        default_factory=RedisSettings,
        description="The `RedisSettings` used to configure the connection to the Redis instance that will store circuit breaker states.",
        alias="REDIS",
    )
