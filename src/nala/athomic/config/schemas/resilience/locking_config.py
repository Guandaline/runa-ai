# src/nala/athomic/config/schemas/resilience/locking_config.py
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from ..database.kvstore.kvstore_config import KVStoreSettings


class RedisLockProviderSettings(BaseModel):
    """Defines the configuration for the Redis-based distributed lock provider.

    This model is used when Redis is the backend for distributed locking.
    It reuses the standard `KVStoreSettings` for its connection configuration.

    Attributes:
        backend (Literal["redis"]): The discriminator field.
        kvstore (KVStoreSettings): The KVStore settings for the Redis connection.
    """

    model_config = ConfigDict(extra="ignore")
    backend: Literal["redis"] = Field(
        default="redis",
        description="The discriminator field identifying this as the Redis lock provider.",
    )

    kvstore: KVStoreSettings = Field(
        default_factory=KVStoreSettings,
        description="The `KVStoreSettings` used to configure the connection to the Redis instance that will manage the locks.",
    )


class InMemoryLockProviderSettings(BaseModel):
    """Defines the configuration for the in-memory (local) lock provider.

    This model selects the in-memory lock provider, which is suitable for local
    development and single-process applications. This lock is not distributed
    and will not coordinate between multiple service instances.

    Attributes:
        backend (Literal["in_memory"]): The discriminator field.
    """

    model_config = ConfigDict(extra="ignore")
    backend: Literal["in_memory"] = Field(
        default="in_memory",
        description="The discriminator field identifying this as the in-memory lock provider.",
    )


class LockingSettings(BaseModel):
    """Defines the configuration for the distributed locking system.

    This model configures the distributed locking feature, which is used to ensure
    mutual exclusion for critical sections of code in a distributed environment.
    It allows for selecting a backend provider (e.g., Redis for distributed
    locks or in-memory for local locks).

    Attributes:
        enabled (bool): A master switch for the locking system.
        lock_timeout_sec (int): The default auto-expiration time for a lock.
        provider (Union[...]): The backend provider configuration for locking.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to globally enable or disable the locking system.",
    )

    lock_timeout_sec: int = Field(
        default=30,
        alias="CACHE_LOCK_TIMEOUT_SEC",
        description="The default time in seconds a distributed lock will be held before it automatically expires. This acts as a safety mechanism to prevent indefinite deadlocks.",
    )

    provider: Annotated[
        Union[RedisLockProviderSettings, InMemoryLockProviderSettings],
        Field(discriminator="backend"),
    ] = Field(
        default_factory=InMemoryLockProviderSettings,
        description="The backend provider configuration for locking, selected via the 'backend' discriminator.",
    )
