from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class FallbackSettings(BaseModel):
    """Defines the configuration for a fallback resilience mechanism.

    This model configures a fallback chain for a primary service, typically a cache.
    When the primary provider fails or misses a key (depending on the read strategy),
    the system will attempt to retrieve the data from a sequence of secondary
    (fallback) providers.

    Attributes:
        enabled (bool): A master switch for the fallback mechanism.
        provider_connection_names (List[str]): An ordered list of KVStore
            connection names to use as fallbacks.
        write_strategy (Literal["write_to_primary", "write_through"]): The
            strategy for write operations.
        read_strategy (Literal["on_error", "on_miss_or_error"]): The
            strategy for read operations.
    """

    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(
        default=False, description="Enables or disables the fallback mechanism."
    )

    provider_connection_names: List[str] = Field(
        default_factory=list,
        alias="PROVIDER_CONNECTION_NAMES",
        description="An ordered list of KVStore connection names (from `database.kvstore`) to be used as fallback providers.",
    )

    write_strategy: Literal["write_to_primary", "write_through"] = Field(
        default="write_to_primary",
        alias="WRITE_STRATEGY",
        description="Defines the behavior for write operations: 'write_to_primary' (write only to the primary provider) or 'write_through' (write to the primary and all fallbacks).",
    )

    read_strategy: Literal["on_error", "on_miss_or_error"] = Field(
        default="on_error",
        alias="READ_STRATEGY",
        description="Defines when to trigger the fallback chain for read operations: 'on_error' (only when the primary fails) or 'on_miss_or_error' (when the primary fails or returns no data).",
    )
