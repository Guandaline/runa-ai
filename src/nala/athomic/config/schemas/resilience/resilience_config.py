# src/nala/athomic/config/schemas/resilience/resilience_config.py
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .adaptive_throttling_config import AdaptiveThrottlingSettings
from .circuit_breaker import CircuitBreakerSettings
from .locking_config import LockingSettings
from .rate_limiter import RateLimiterSettings
from .retry_config import RetrySettings


class ResilienceSettings(BaseModel):
    """Defines the top-level configuration for all resilience patterns.

    This model aggregates the configurations for all resilience features
    provided by the Athomic framework. These patterns help build robust and
    fault-tolerant applications by managing failures, retries, concurrency,
    and other challenges in distributed systems.

    Attributes:
        idempotency (Optional[IdempotencySettings]): Configures the idempotency mechanism.
        sagas (Optional[SagaSettings]): Configures the Saga distributed transaction pattern.
        circuit_breaker (Optional[CircuitBreakerSettings]): Configures the Circuit Breaker pattern.
        rate_limiter (Optional[RateLimiterSettings]): Configures the Rate Limiter.
        adaptive_throttling (Optional[AdaptiveThrottlingSettings]): Configures Adaptive Throttling.
        fallback (Optional[FallbackSettings]): Configures the Fallback mechanism.
        locking (Optional[LockingSettings]): Configures the distributed locking provider.
        leasing (Optional[LeasingSettings]): Configures the distributed leasing mechanism.
        bulkhead (Optional[BulkheadSettings]): Configures the Bulkhead (concurrency limiting) pattern.
        retry (Optional[RetrySettings]): Configures the automatic retry mechanism.
        backoff (Optional[BackoffSettings]): Configures the exponential backoff strategy.
        sharding (Optional[ShardingSettings]): Configures the distributed workload sharding mechanism.
        backpressure (Optional[BackpressureSettings]): Configures the dynamic backpressure mechanism.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    circuit_breaker: Optional[CircuitBreakerSettings] = Field(
        default_factory=CircuitBreakerSettings,
        alias="CIRCUIT_BREAKER",
        description="Configuration for the Circuit Breaker pattern, which prevents repeated calls to a failing service.",
    )

    rate_limiter: Optional[RateLimiterSettings] = Field(
        default=None,
        alias="RATE_LIMITER",
        description="Configuration for the Rate Limiter, used to control the frequency of operations.",
    )

    adaptive_throttling: Optional[AdaptiveThrottlingSettings] = Field(
        default=None,
        alias="ADAPTIVE_THROTTLING",
        description="Configuration for Adaptive Throttling, which dynamically adjusts rate limits based on system health.",
    )

    locking: Optional[LockingSettings] = Field(
        default_factory=LockingSettings,
        alias="LOCKING",
        description="Configuration for the distributed locking provider, used for mutual exclusion.",
    )
    retry: Optional[RetrySettings] = Field(
        default_factory=RetrySettings,
        alias="RETRY",
        description="Configuration for the automatic retry mechanism for failed operations.",
    )

    @field_validator("circuit_breaker")
    @classmethod
    def check_circuit_keys(
        cls, v: Optional[CircuitBreakerSettings]
    ) -> Optional[CircuitBreakerSettings]:
        """A Pydantic validator to ensure that circuit breaker names are valid strings.

        Args:
            cls: The class being validated.
            v (Optional[CircuitBreakerSettings]): The value of the `circuit_breaker` field.

        Returns:
            Optional[CircuitBreakerSettings]: The validated `circuit_breaker` field value.

        Raises:
            ValueError: If a key in the `circuits` dictionary is not a non-empty string.
        """
        if v and v.circuits:
            for key in v.circuits.keys():
                if not isinstance(key, str) or not key:
                    raise ValueError(
                        f"Circuit name (key) in 'circuits' must be a non-empty string, got: {key}"
                    )
        return v
