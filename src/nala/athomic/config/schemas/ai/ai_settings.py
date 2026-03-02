# src/nala/athomic/config/schemas/ai/ai_settings.py
"""
Top-level configuration for the AI Foundation module.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)

from ..base_settings import ConnectionGroupSettings
from .agents.agent_settings import AgentsSettings
from .governance.governance_settings import GovernanceSettings
from .llm.llm_settings import LLMConnectionSettings
from .prompts.prompts_settings import PromptSettings
from .workflow.workflow_settings import WorkflowSettings


class AISettings(BaseModel):
    """
    The root configuration for all AI-related services in Athomic.

    This model orchestrates multiple AI connections (LLMs, Embeddings) allowing
    the application to switch between providers (e.g., Vertex, OpenAI) seamlessly.

    Attributes:
        enabled: Master switch for the AI module.
        connections: A group of named settings for AI providers (e.g., 'default', 'gpt4').
        default_connection_name: The name of the connection to use when none is specified.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Master switch to enable or disable AI capabilities.",
    )

    prompts: PromptSettings = Field(
        default_factory=PromptSettings,
        alias="PROMPTS",
        description="Configuration for Prompt Engineering module.",
    )

    connections: ConnectionGroupSettings[LLMConnectionSettings] = Field(
        default_factory=ConnectionGroupSettings,
        alias="CONNECTIONS",
        description="A registry of named AI connections. Usage: ai.connections.get('default').",
    )

    default_connection_name: str = Field(
        default="default",
        alias="DEFAULT_CONNECTION_NAME",
        description="The name of the connection to use for general purpose generation.",
    )

    agents: Optional[AgentsSettings] = Field(
        default=None,
        alias="AGENTS",
        description="Configuration for AI Agents module.",
    )

    cognitive: Optional[CognitiveSettings] = Field(
        default=None,
        alias="COGNITIVE",
        description="Configuration for Cognitive Services (Intent/NLU) module.",
    )

    governance: Optional[GovernanceSettings] = Field(
        default_factory=GovernanceSettings,
        alias="GOVERNANCE",
        description="Configuration for the AI governance and guardrails module.",
    )

    workflow: Optional[WorkflowSettings] = Field(
        default=None,
        alias="WORKFLOW",
        description="Configuration for the Workflow Orchestration Engine.",
    )
