# src/nala/athomic/config/schemas/resilience/sagas_config.py
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.enums.defaults import Defaults


class SagaReaperSettings(BaseModel):
    """Defines the configuration for the Saga Reaper service.

    The Saga Reaper is a background service that finds and initiates recovery
    for saga instances that have become stalled (i.e., have not been updated
    for a configured period).

    Attributes:
        enabled (bool): Enables the background service for saga recovery.
        poll_interval_seconds (int): How often the reaper scans for stalled sagas.
        stalled_threshold_seconds (int): The duration after which a saga is
            considered stalled.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enables the background service that recovers stalled sagas.",
    )
    poll_interval_seconds: int = Field(
        default=300,  # 5 minutes
        alias="POLL_INTERVAL_SECONDS",
        description="How often the reaper scans for stalled sagas.",
    )
    stalled_threshold_seconds: int = Field(
        default=900,  # 15 minutes
        alias="STALLED_THRESHOLD_SECONDS",
        description="Duration in seconds after which a non-updated saga is considered stalled.",
    )


class SagaSettings(BaseModel):
    """Defines the configuration for the Saga distributed transaction pattern.

    This model configures the Saga pattern, which manages long-running, multi-step
    business processes across different services. It supports both orchestration and
    choreography execution models and includes a 'reaper' service for recovering
    stalled transactions.

    Attributes:
        enabled (Optional[bool]): A master switch for the Saga pattern features.
        executor_type (Literal["orchestration", "choreography"]): The execution
            strategy for sagas.
        reaper (SagaReaperSettings): Settings for the saga recovery service.
        key_prefix (str): The key prefix for saga state entries in the KV store.
        index_key (str): The key for the sorted set used to index sagas by time.
        kv_store_connection_name (str): The named KVStore connection to use for
            persisting saga state.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: Optional[bool] = Field(
        default=True,
        alias="ENABLED",
        description="Enables the Saga resilience pattern features.",
    )

    executor_type: Literal["orchestration", "choreography"] = Field(
        default="orchestration",
        alias="EXECUTOR_TYPE",
        description="Defines the execution strategy for sagas: 'orchestration' (central coordinator) or 'choreography' (event-driven).",
    )
    messaging_connection_name: str = Field(
        default=Defaults.DEFAULT_MESSAGING_CONNECTION,
        alias="CONNECTION_NAME",
        description="The named KVStore connection (from `database.kvstore`) to use for persisting saga state.",
    )

    reaper: SagaReaperSettings = Field(
        default_factory=SagaReaperSettings,
        alias="REAPER",
        description="Settings for the saga recovery service (reaper).",
    )
    key_prefix: str = Field(
        default="sagas:state",
        alias="KEY_PREFIX",
        description="The key prefix for saga state entries in the KV store.",
    )
    index_key: str = Field(
        default="sagas:index:updated_at",
        alias="INDEX_KEY",
        description="The key for the sorted set used to index sagas by their last update time, for efficient reaper scanning.",
    )

    kv_store_connection_name: str = Field(
        default="default_redis",
        alias="KV_STORE_CONNECTION_NAME",
        description="The named KVStore connection (from `database.kvstore`) to use for persisting saga state.",
    )
