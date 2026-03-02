# src/nala/athomic/config/schemas/resilience/rate_limiter/rate_limiter_config.py
from typing import Annotated, Dict, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .providers import LimitsProviderSettings, RedisLimiterProviderSettings


class RateLimiterSettings(BaseModel):
    """Defines the configuration for the rate limiting resilience feature.

    This model configures the rate limiter, which controls the frequency of
    operations to prevent system overload or abuse. It uses a policy-based
    approach, where different limits can be defined for various use cases.

    Attributes:
        enabled (bool): A master switch for the rate limiter.
        namespace (Optional[str]): A namespace for rate limiting keys.
        backend (Literal["limits", "redis"]): The underlying provider to use.
        provider (Union[...]): The backend-specific provider configuration.
        key_prefix (Optional[str]): A static prefix for keys in the backend.
        default_policy_limit (Optional[str]): The default rate limit to apply.
        policies (Optional[Dict[str, str]]): A dictionary mapping policy names
            to rate limit strings.
    """

    model_config = ConfigDict(
        extra="ignore", validate_assignment=True, populate_by_name=True
    )

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to globally enable or disable the rate limiter.",
    )

    namespace: Optional[str] = Field(
        default="rate_limiter",
        alias="NAMESPACE",
        description="An optional namespace used by the `ContextKeyGenerator` for creating the final rate limit key.",
    )

    backend: Literal["limits", "redis"] = Field(
        default="limits",
        alias="BACKEND",
        description="The underlying provider to use for rate limiting. This acts as the discriminator for the `provider` field.",
    )

    provider: Annotated[
        Union[LimitsProviderSettings, RedisLimiterProviderSettings],
        Field(discriminator="backend"),
    ] = Field(
        default_factory=LimitsProviderSettings,
        description="A discriminated union holding the specific configuration for the chosen backend.",
    )

    key_prefix: Optional[str] = Field(
        default="nala:ratelimit",
        alias="KEY_PREFIX",
        description="A static string to prepend to all keys stored in the rate limiting backend.",
    )

    default_policy_limit: Optional[str] = Field(
        default="100/hour",
        alias="DEFAULT_POLICY_LIMIT",
        description="The default rate limit string (e.g., '100/hour') to apply if a more specific policy is not found.",
    )

    policies: Optional[Dict[str, str]] = Field(
        default=None,
        alias="POLICIES",
        description="A dictionary that maps policy names to their corresponding rate limit strings (e.g., {'free_tier': '50/minute'}).",
    )
