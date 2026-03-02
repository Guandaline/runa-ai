# src/nala/athomic/ai/domain/tools.py
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolOutput(BaseModel):
    """
    Standardized result of a tool execution.
    This object flows from the Tool Executor back to the Agent Service.
    """

    tool_call_id: str = Field(
        ..., description="The ID of the ToolCall this output belongs to."
    )
    name: str = Field(..., description="The name of the tool executed.")
    content: str = Field(..., description="The string result of the tool execution.")
    is_error: bool = Field(
        False, description="Flag indicating if the execution failed."
    )

    # Optional structured result for internal logic (not usually sent to LLM)
    result_metadata: Optional[Any] = None


class ToolCall(BaseModel):
    """
    Represents a normalized request from the LLM to execute a tool.
    Agnostic of the underlying provider (Vertex/OpenAI).
    """

    id: str = Field(
        ...,
        description="Unique identifier for this tool call (if provided by backend).",
    )
    name: str = Field(..., description="The name of the tool to call.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Parsed arguments for the tool."
    )
