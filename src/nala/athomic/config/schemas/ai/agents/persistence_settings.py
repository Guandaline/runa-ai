# src/nala/athomic/config/schemas/ai/agents/persistence_settings.py
from typing import Literal

from pydantic import BaseModel, Field


class AgentPersistenceSettings(BaseModel):
    """
    Configuration for Agent State Persistence.

    This module configures how agent execution state is saved.
    It is decoupled from the underlying storage technology (Redis, Memory, etc.),
    which is defined in the [database] section of the settings.
    """

    enabled: bool = Field(
        default=True,
        description="Master switch to enable or disable state persistence.",
    )

    # Defines the architectural strategy.
    strategy: Literal["kv_store"] = Field(
        default="kv_store",
        description="The persistence strategy implementation to use.",
    )

    # --- Connection Reference ---

    connection_name: str = Field(
        default="default_local",
        description=(
            "The logical name of the connection to use. "
            "For strategy='kv_store', this must match a key in [database.kvstore]."
        ),
    )

    # --- Persistence Logic Settings ---

    namespace: str = Field(
        default="agent_checkpoints",
        description="Logical namespace/prefix for organizing checkpoints.",
    )

    ttl_seconds: int = Field(
        default=604800,  # 7 days
        description="Time-To-Live in seconds for stored checkpoints.",
    )
