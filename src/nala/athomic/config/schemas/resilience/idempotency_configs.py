from pydantic import BaseModel, ConfigDict, Field

from ..database.kvstore.kvstore_config import KVStoreSettings


class IdempotencySettings(BaseModel):
    """Defines the configuration for the idempotency resilience feature.

    This model configures the idempotency mechanism, which ensures that
    operations can be safely retried without producing duplicate side effects.
    It relies on a distributed lock to prevent race conditions and a KV store
    to persist the results of the first successful operation for a given key.

    Attributes:
        enabled (bool): A master switch for the idempotency feature.
        default_ttl_seconds (int): The default TTL for stored results.
        default_lock_timeout_seconds (int): The default time to wait for a lock.
        kvstore (KVStoreSettings): The KVStore configuration for storing results
            and managing locks.
    """

    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to globally enable or disable the idempotency feature.",
    )

    ttl_seconds: int = Field(
        default=86400,  # 24 hours
        alias="TTL_SECONDS",
        description="The default Time-To-Live (TTL) in seconds for stored idempotency results.",
    )

    lock_timeout_seconds: int = Field(
        default=10,
        alias="LOCK_TIMEOUT_SECONDS",
        description="The default time in seconds to wait for a distributed lock before raising an `IdempotencyConflictError`.",
    )

    kvstore: KVStoreSettings = Field(
        default_factory=KVStoreSettings,
        description="The `KVStoreSettings` used to configure the backend for both storing idempotent results and managing distributed locks.",
    )
