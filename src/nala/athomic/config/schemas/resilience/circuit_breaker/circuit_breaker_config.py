from typing import Annotated, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .circuit_breaker_storage_config import (
    LocalCircuitBreakerStorageSettings,
    RedisCircuitBreakerStorageSettings,
)


class CircuitSpecificSettings(BaseModel):
    """Defines the specific override settings for a single, named circuit.

    This model allows for fine-tuning the behavior of an individual circuit
    breaker, overriding the global defaults. As it inherits from `LiveConfigModel`,
    these thresholds can be adjusted at runtime.

    Attributes:
        circuit_name (str): The unique name of the circuit.
        fail_max (Optional[int]): The failure threshold to open this circuit.
        reset_timeout_sec (Optional[float]): The open-state duration for
            this circuit.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    circuit_name: str = Field(
        default="nala_circuit",
        description="The unique name of the circuit to which these settings apply.",
        alias="CIRCUIT_NAME",
    )

    fail_max: Optional[int] = Field(
        default=None,
        description="The number of failures required to open this specific circuit, overriding the default.",
        alias="FAIL_MAX",
    )

    reset_timeout_sec: Optional[float] = Field(
        default=None,
        description="The time in seconds this specific circuit will remain open before transitioning to half-open, overriding the default.",
        alias="RESET_TIMEOUT_SEC",
    )


class CircuitBreakerSettings(BaseModel):
    """Defines the configuration for the Circuit Breaker resilience module.

    This model configures the circuit breaker pattern, which helps prevent
    repeated calls to a failing service. It sets up the default behavior for all
    circuits and allows for specific overrides on a per-circuit basis. It also
    configures the storage backend for circuit states.

    Attributes:
        enabled (bool): A master switch for the circuit breaker functionality.
        namespace (Optional[str]): A prefix for storage keys to prevent collisions.
        default_circuit_name (str): The default name for a circuit.
        default_fail_max (int): The default failure threshold to open a circuit.
        default_reset_timeout_sec (float): The default open-state duration.
        circuits (Optional[Dict[str, CircuitSpecificSettings]]): A dictionary of
            specific overrides for named circuits.
        provider (Union[...]): The storage backend for persisting circuit breaker states.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to globally enable or disable the Circuit Breaker functionality.",
    )
    namespace: Optional[str] = Field(
        default="cb",
        alias="NAMESPACE",
        description="An optional namespace prepended to storage keys, used to isolate states in a shared backend like Redis.",
    )
    default_circuit_name: str = Field(
        default="nala_circuit",
        alias="DEFAULT_CIRCUIT_NAME",
        description="The default name to use for a circuit if not explicitly provided in a decorator.",
    )
    default_fail_max: int = Field(
        default=5,
        alias="DEFAULT_FAIL_MAX",
        description="The default number of failures required to open a circuit.",
    )
    default_reset_timeout_sec: float = Field(
        default=30.0,
        alias="DEFAULT_RESET_TIMEOUT_SEC",
        description="The default time in seconds a circuit will remain open before transitioning to half-open.",
    )
    circuits: Optional[Dict[str, CircuitSpecificSettings]] = Field(
        default=None,
        alias="CIRCUITS",
        description="A dictionary of specific configurations that override the defaults for named circuits.",
    )

    provider: Annotated[
        Union[LocalCircuitBreakerStorageSettings, RedisCircuitBreakerStorageSettings],
        Field(discriminator="backend"),
    ] = Field(
        default_factory=LocalCircuitBreakerStorageSettings,
        description="The storage backend for persisting circuit breaker states, selected via the 'backend' discriminator.",
    )
