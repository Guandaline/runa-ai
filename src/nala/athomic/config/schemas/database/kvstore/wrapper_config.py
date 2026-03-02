from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DefaultTTLWrapperSettings(BaseModel):
    """Defines the configuration for the Default TTL wrapper.

    This schema configures a wrapper that applies a default Time-To-Live (TTL)
    to key-value pairs when they are written to the store, if no other TTL is
    specified in the `set` operation.

    Attributes:
        enabled (bool): Enables or disables this wrapper.
        name (Literal["default_ttl"]): The unique name that identifies this
            wrapper type, used as a discriminator.
        default_ttl_seconds (Optional[int]): The default Time-To-Live in
            seconds to apply to keys.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    enabled: bool = Field(default=True, description="Enables or disables this wrapper.")
    name: Literal["default_ttl"] = Field(
        default="default_ttl",
        description="The unique name that identifies this wrapper type, used as a discriminator.",
    )
    default_ttl_seconds: Optional[int] = Field(
        default=3600,
        description="The default Time-To-Live in seconds to apply to keys.",
    )


class KeyResolvingWrapperSettings(BaseModel):
    """Defines the configuration for the Key Resolving wrapper.

    This schema configures a wrapper that automatically generates context-aware
    keys using the `ContextKeyGenerator`. It prepends namespaces and prefixes
    to keys before they are sent to the storage backend.

    Attributes:
        enabled (bool): Enables or disables this wrapper.
        name (Literal["key_resolver"]): The unique name that identifies this
            wrapper type, used as a discriminator.
        namespace (Optional[str]): A specific namespace for the key generator
            to use, overriding global settings.
        static_prefix (Optional[str]): A specific static prefix for the key
            generator to use, overriding global settings.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=False, description="Enables or disables this wrapper."
    )
    name: Literal["key_resolver"] = Field(
        default="key_resolver",
        description="The unique name that identifies this wrapper type, used as a discriminator.",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="A specific namespace for the key generator to use, overriding global settings.",
    )
    static_prefix: Optional[str] = Field(
        default=None,
        description="A specific static prefix for the key generator to use, overriding global settings.",
    )
