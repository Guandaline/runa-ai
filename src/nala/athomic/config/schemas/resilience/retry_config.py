# src/nala/athomic/config/schemas/resilience/retry_config.py
from typing import Dict, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicySettings(BaseModel):
    """Defines the settings for a single, named retry policy.

    This model encapsulates all parameters for a specific retry strategy,
    including the number of attempts, the delay logic (min/max wait, backoff
    factor, jitter), and which exceptions should trigger a retry.

    Attributes:
        attempts (int): Maximum number of retry attempts.
        wait_min_seconds (float): Minimum wait time between retries in seconds.
        wait_max_seconds (float): Maximum wait time for exponential backoff in seconds.
        backoff (float): The multiplier for exponential backoff.
        exceptions (Tuple[str, ...]): A tuple of exception class names that
            should trigger a retry.
        timeout (Optional[float]): Maximum timeout in seconds for each attempt.
        jitter (Optional[float]): A factor of randomness (0.0 to 1.0) applied
            to the delay.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    attempts: int = Field(
        3,
        alias="ATTEMPTS",
        description="Maximum number of times to retry an operation.",
    )

    wait_min_seconds: float = Field(
        1.0,
        alias="WAIT_MIN",
        description="The minimum wait time between retries in seconds.",
    )

    wait_max_seconds: float = Field(
        10.0,
        alias="WAIT_MAX",
        description="The maximum wait time to cap the exponential backoff in seconds.",
    )

    backoff: float = Field(
        1.0,
        alias="BACKOFF",
        description="The multiplier for increasing the delay in an exponential backoff strategy.",
    )

    exceptions: Tuple[str, ...] = Field(
        ("Exception",),
        alias="EXCEPTIONS",
        description="A tuple of exception class names that should trigger a retry.",
    )

    timeout: Optional[float] = Field(
        None,
        alias="TIMEOUT",
        description="An optional timeout in seconds for each individual attempt.",
    )

    jitter: Optional[float] = Field(
        None,
        alias="JITTER",
        description="A factor of randomness (e.g., 0.1 for 10%) applied to the delay to prevent thundering herds.",
    )


class RetrySettings(BaseModel):
    """Defines the configuration for the automatic retry mechanism.

    This model configures the retry feature, which automatically re-executes
    failed operations based on defined policies. It supports a default policy
    and named overrides for different operational contexts.

    Attributes:
        enabled (bool): A master switch for the retry mechanism.
        default_policy (RetryPolicySettings): The default retry policy to use.
        policies (Dict[str, RetryPolicySettings]): A dictionary of named,
            override retry policies.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to globally enable or disable the retry mechanism.",
    )

    default_policy: RetryPolicySettings = Field(
        default_factory=RetryPolicySettings,
        alias="DEFAULT_POLICY",
        description="The default retry policy to use if a specific one is not requested.",
    )

    policies: Dict[str, RetryPolicySettings] = Field(
        default_factory=dict,
        alias="POLICIES",
        description="A dictionary of named, override retry policies for specific use cases.",
    )
