# src/nala/athomic/ai/schemas/chat.py
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    """Standardized roles for chat messages across the framework."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """
    Represents a single message in the conversation history.
    This entity is shared between Agents, LLMs, and Memory systems.
    """

    model_config = ConfigDict(populate_by_name=True)

    role: MessageRole
    content: Optional[str] = None
    name: Optional[str] = Field(
        None, description="Name of the author (optional) or tool name."
    )
    tool_call_id: Optional[str] = Field(
        None, description="ID of the tool call this message responds to."
    )

    # Metadata for observability or provider-specific usage
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
