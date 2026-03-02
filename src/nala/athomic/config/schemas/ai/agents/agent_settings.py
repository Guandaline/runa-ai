# src/nala/athomic/config/schemas/ai/agents/agent_settings.py
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.ai.agents.persistence_settings import (
    AgentPersistenceSettings,
)
from nala.athomic.config.schemas.base_settings import ConnectionGroupSettings


class AgentProfileSettings(BaseModel):
    """
    Configuration for a specific Agent Profile.
    Defines the behavior, capabilities, and constraints of a single agent type.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Standard Connection fields (inherited concept from ConnectionGroup items)
    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enables or disables this specific agent profile.",
    )

    # Identity & Behavior
    name: str = Field(..., description="Unique logical name for this agent profile.")
    description: Optional[str] = Field(
        None, description="Description of the agent's purpose."
    )
    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        alias="SYSTEM_PROMPT",
        description="The system instruction (persona) for the agent.",
    )

    # Connection Binding (Explicit Architecture)
    connection_name: Optional[str] = Field(
        default=None,
        alias="CONNECTION_NAME",
        description=(
            "The specific LLM connection ID to use (defined in ai.connections). "
            "If None, uses the module's default."
        ),
    )

    # Model Overrides (Runtime Patching)
    model_name: Optional[str] = Field(
        default=None,
        alias="MODEL_NAME",
        description="Override the model used by the LLM connection (e.g. use 'gpt-4' instead of 'gpt-3.5').",
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        alias="TEMPERATURE",
        description="Override the sampling temperature.",
    )

    # Execution Constraints
    max_iterations: int = Field(
        default=10,
        gt=0,
        alias="MAX_ITERATIONS",
        description="Safety limit for the maximum number of Think/Act loops.",
    )
    max_execution_time_seconds: int = Field(
        default=60,
        alias="MAX_EXECUTION_TIME_SECONDS",
        description="Hard timeout for the total agent execution.",
    )

    # Tools & Capabilities
    tools: List[str] = Field(
        default_factory=list,
        alias="TOOLS",
        description="List of tool names (registered in ToolRegistry) this agent can access.",
    )

    # Memory
    memory_key: str = Field(
        default="short_term",
        alias="MEMORY_KEY",
        description="The key/type of memory backend to use (mapped in MemoryManager).",
    )
    max_history_messages: int = Field(
        default=20,
        alias="MAX_HISTORY_MESSAGES",
        description="Maximum number of past messages to include in the context window.",
    )


class AgentsSettings(BaseModel):
    """
    Container for all Agent configurations.
    Uses ConnectionGroupSettings to manage multiple named profiles consistently.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Master switch for the Agents module.",
    )

    default_profile: str = Field(
        default="default",
        alias="DEFAULT_PROFILE",
        description="The name of the profile to use if none is specified in the factory.",
    )

    default_connection_name: str = Field(
        default="default",
        alias="DEFAULT_CONNECTION_NAME",
        description="The default LLM connection to use if an agent profile doesn't specify one.",
    )

    profiles: ConnectionGroupSettings[AgentProfileSettings] = Field(
        default_factory=ConnectionGroupSettings,
        alias="PROFILES",
        description="A registry of named Agent Profiles.",
    )

    persistence: Optional[AgentPersistenceSettings] = Field(
        default=None,
        alias="PERSISTENCE",
        description="Configuration for Agent State Persistence.",
    )
