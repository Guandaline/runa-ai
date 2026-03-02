# src/nala/athomic/config/schemas/resilience/backoff_config.py
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class BackoffPolicySettings(BaseModel):
    """Defines the settings for a single, named exponential backoff policy.

    This model encapsulates the parameters for an exponential backoff strategy,
    controlling the initial delay, the maximum delay, and the rate at which
    the delay increases.

    Attributes:
        min_delay_seconds (float): The initial and minimum delay in seconds.
        max_delay_seconds (float): The maximum delay to cap the backoff.
        factor (float): The multiplier for increasing the delay after each attempt.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    min_delay_seconds: float = Field(
        1.0, description="The initial and minimum delay in seconds."
    )
    max_delay_seconds: float = Field(
        30.0, description="The maximum delay in seconds to cap the backoff."
    )
    factor: float = Field(
        1.5, description="The multiplier for increasing the delay after each attempt."
    )


class BackoffSettings(BaseModel):
    """Defines the configuration for the exponential backoff mechanism.

    This model configures the exponential backoff feature, which is used to
    intelligently manage delays in polling loops or retry attempts. It supports
    a default policy and named overrides for different use cases. As it inherits
    from `LiveConfigModel`, these policies can be tuned at runtime.

    Attributes:
        enabled (bool): A master switch for the backoff mechanism.
        default_policy (BackoffPolicySettings): The default backoff policy.
        policies (Dict[str, BackoffPolicySettings]): A dictionary of named,
            override backoff policies.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to enable or disable the backoff mechanism globally.",
    )
    default_policy: BackoffPolicySettings = Field(
        default_factory=BackoffPolicySettings,
        description="The default backoff policy to use if a specific one is not requested.",
    )
    policies: Dict[str, BackoffPolicySettings] = Field(
        default_factory=dict,
        description="A dictionary of named, override backoff policies for specific use cases.",
    )
