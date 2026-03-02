# src/nala/athomic/config/schemas/database/kvstore/local_config.py
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LocalSettings(BaseModel):
    """Configuration settings for the Local Memory KVStore backend.

    This model defines the configuration for the in-memory Key-Value store provider
    (LocalKVClient), which is primarily used for development, testing, and single-instance
    scenarios. It currently requires no unique parameters, but includes optional fields
    for structural consistency with network-based providers.

    Attributes:
        namespace (Optional[str]): Optional namespace for keys, used by the key resolver (inherited from KVStore structure).
        key_prefix (Optional[str]): Optional static key prefix for keys, used by the key resolver (inherited from KVStore structure).
        backend (Literal["local"]): Discriminator field identifying the local memory backend.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    namespace: Optional[str] = Field(
        default=None,
        alias="NAMESPACE",
        description="Optional namespace for keys, used by the key resolver.",
    )

    key_prefix: Optional[str] = Field(
        default=None,
        alias="KEY_PREFIX",
        description="Optional static key prefix for keys.",
    )

    backend: Literal["local"] = "local"
