# src/nala/athomic/config/schemas/resilience/backpressure_config.py
from pydantic import BaseModel, ConfigDict, Field


class BackpressureSettings(BaseModel):
    """Defines the configuration for the dynamic backpressure mechanism.

    This model configures the backpressure system, which is used to temporarily
    stop sending work to a downstream resource that is showing signs of failure.
    The state is managed in a distributed KV store.

    Attributes:
        enabled (bool): A master switch for the backpressure mechanism.
        default_ttl_seconds (int): The default duration to apply backpressure.
        key_prefix (str): The key prefix for backpressure flags in the KV store.
        kv_store_connection_name (str): The name of the KVStore connection to use.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to globally enable or disable the dynamic backpressure mechanism.",
    )

    default_ttl_seconds: int = Field(
        default=30,
        gt=0,
        description="The default duration in seconds to apply backpressure to a resource after a failure is detected.",
    )

    key_prefix: str = Field(
        default="athomic:backpressure",
        description="The key prefix used for storing backpressure state flags in the configured KV store.",
    )

    kv_store_connection_name: str = Field(
        default="default_redis",
        description="The name of the KVStore connection (from `database.kvstore`) used to manage the backpressure state.",
    )
