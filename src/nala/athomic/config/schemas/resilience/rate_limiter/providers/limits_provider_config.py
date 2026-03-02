from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LimitsProviderSettings(BaseModel):
    """Configuration settings for the rate limiter based on the external 'limits' library.

    This model defines the internal components and operational mode for the
    `LimitsRateLimiter` provider, including the choice of algorithm (strategy)
    and state storage backend.

    Attributes:
        backend (Literal["limits"]): Discriminator field identifying the 'limits' library provider.
        strategy (Literal): The rate limiting algorithm/strategy to enforce ('fixed-window' or 'moving-window').
        storage_backend (Literal): The persistence backend to store rate limit counters ('memory' for local, 'redis' for distributed).
        redis_storage_uri (Optional[str]): The Redis connection URI, required if 'storage_backend' is set to 'redis'.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["limits"] = "limits"

    strategy: Literal["fixed-window", "moving-window"] = Field(
        default="fixed-window",
        alias="LIMITS_STRATEGY",
        description="Rate limiting strategy ('fixed-window' or 'moving-window').",
    )

    storage_backend: Literal["memory", "redis"] = Field(
        default="memory",
        alias="LIMITS_STORAGE_BACKEND",
        description="Storage backend to use ('memory' or 'redis').",
    )

    redis_storage_uri: Optional[str] = Field(
        default=None,
        alias="LIMITS_REDIS_URI",
        description="Redis connection URI (e.g., redis://localhost:6379/1). Used only if 'storage_backend' is 'redis'",
    )
