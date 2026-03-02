# src/nala/athomic/config/schemas/database/kvstore/kvstore_config.py

from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.enums.defaults import Defaults

from .providers import LocalSettings, RedisSettings
from .wrapper_config import DefaultTTLWrapperSettings, KeyResolvingWrapperSettings

wrapper_types = Annotated[
    Union[DefaultTTLWrapperSettings, KeyResolvingWrapperSettings],
    Field(discriminator="name"),
]


class KVStoreSettings(BaseModel):
    """Defines the configuration for a single Key-Value (KV) store connection.

    This model configures a complete KV client instance, including its backend
    provider (e.g., Redis), a chain of decorator-like wrappers for added
    functionality, and specific behaviors like key generation and serialization.

    Attributes:
        enabled (bool): Toggles this specific KV store connection on or off.
        wrappers (Optional[List[wrapper_types]]): A list of wrappers to be
            applied to the base KV client.
        apply_key_resolver (bool): A flag to automatically apply a key resolver.
        namespace (Optional[str]): The namespace for the key resolver.
        key_prefix (Optional[str]): A static prefix for the key resolver.
        connect_timeout (float): Connection timeout in seconds.
        provider (Union[RedisSettings, LocalSettings]): The backend-specific
            provider configuration.
        serializer (Optional[SerializerSettings]): The serializer configuration
            for this specific KV store instance.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enables or disables this specific KV store connection.",
    )

    connection_name: Optional[str] = Field(
        default=Defaults.DEFAULT_REDIS_CONNECTION,
        description="The unique name of this connection, injected by the manager at runtime.",
    )

    wrappers: Optional[List[wrapper_types]] = Field(
        default_factory=list,
        description="A list of decorator-like wrappers to be applied to the base KVStore client in the specified order.",
    )

    apply_key_resolver: bool = Field(
        default=True,
        alias="APPLY_KEY_RESOLVER",
        description="A convenience flag to automatically apply a `KeyResolvingKVClient` wrapper. May be deprecated in favor of explicitly adding to the `wrappers` list.",
    )

    namespace: Optional[str] = Field(
        default=None,
        alias="NAMESPACE",
        description="The namespace to be used by the `ContextKeyGenerator` when the key resolver wrapper is active.",
    )

    key_prefix: Optional[str] = Field(
        default=None,
        alias="KEY_PREFIX",
        description="The static key prefix to be used by the `ContextKeyGenerator`, overriding global context settings if set.",
    )

    connect_timeout: float = Field(
        default=15.0,
        alias="CONNECT_TIMEOUT",
        description="Timeout in seconds for establishing a connection to the KVStore backend.",
    )

    provider: Annotated[
        Union[RedisSettings, LocalSettings],
        Field(discriminator="backend"),
    ] = Field(
        default_factory=LocalSettings,
        description="A discriminated union holding the specific configuration for the chosen backend (e.g., `RedisSettings`).",
    )
