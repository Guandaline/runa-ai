from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ....models import secrets_types


class RedisSettings(BaseModel):
    """Specific settings for Redis connection.

    This model defines all configuration parameters necessary to establish a
    secure and reliable connection to a Redis Key-Value store instance. It
    supports configuring the connection via a complete URI or through
    individual fields (host, port, user, password).

    Attributes:
        enabled (bool): Flag to enable or disable the use of Redis as the KVStore backend.
        uri (Optional[secrets_types]): Complete connection URI (can be a secret reference). Takes precedence over individual fields if provided.
        host (str): The hostname or IP address of the Redis server.
        port (int): The port number for the Redis server.
        db (int): The Redis database index to use (0-15).
        user (Optional[str]): The username for Redis authentication (if applicable).
        password (Optional[secrets_types]): The password for authentication (can be a secret reference).
        namespace (Optional[str]): Optional namespace for Redis keys, used by the key resolver.
        key_prefix (Optional[str]): Optional static key prefix for all Redis keys, used by the key resolver.
        decode_responses (bool): If True, automatically decodes Redis responses to UTF-8 strings.
        socket_connect_timeout (Optional[int]): Timeout (in seconds) for establishing the TCP connection.
        backend (Literal["redis"]): Discriminator field indicating the Redis backend.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=False,
        alias="ENABLED",
        description="Enable or disable the use of Redis as the KVStore backend.",
    )

    # --- Option 1: Complete URI (Can be a secret) ---
    uri: Optional[secrets_types] = Field(
        default=None,
        alias="URI",
        description="Complete Redis connection URI. If provided, it takes precedence over individual fields.",
    )

    # --- Option 2: Deconstructed Fields ---
    host: str = Field(default="localhost", alias="HOST")
    port: int = Field(default=6379, alias="PORT")
    db: int = Field(default=0, alias="DB")
    user: Optional[str] = Field(default=None, alias="USER")

    password: Optional[secrets_types] = Field(default=None, alias="PASSWORD")

    namespace: Optional[str] = Field(
        default=None,
        alias="NAMESPACE",
        description="Optional namespace for Redis keys.",
    )

    key_prefix: Optional[str] = Field(
        default=None,
        alias="KEY_PREFIX",
        description="Optional static key prefix for Redis keys.",
    )

    decode_responses: bool = Field(
        default=True,
        alias="DECODE_RESPONSES",
        description="Automatically decode Redis responses to UTF-8.",
    )

    socket_connect_timeout: Optional[int] = Field(
        default=5,
        alias="CONNECT_TIMEOUT",
        description="Timeout (seconds) for establishing connection.",
    )

    backend: Literal["redis"] = "redis"
