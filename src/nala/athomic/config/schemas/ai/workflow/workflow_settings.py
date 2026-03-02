from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkflowSettings(BaseModel):
    """
    Configuration for the Workflow Orchestration Engine.
    Controls the behavior of agentic flows, graph execution, and runtime limits.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Master switch to enable the Workflow Engine.",
    )

    default_provider: Literal["langgraph", "langchain", "memory"] = Field(
        default="langgraph",
        alias="DEFAULT_PROVIDER",
        description="The default execution engine backend (e.g., 'langgraph' for cyclic graphs).",
    )

    max_execution_steps: int = Field(
        default=50,
        alias="MAX_EXECUTION_STEPS",
        description="Safety limit for the maximum number of steps a workflow can take (prevents infinite loops).",
    )

    debug_mode: bool = Field(
        default=False,
        alias="DEBUG_MODE",
        description="If True, enables verbose logging and step-by-step tracing of the graph.",
    )
