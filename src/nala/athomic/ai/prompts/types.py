from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptTemplate(BaseModel):
    """
    Represents the raw definition of a prompt loaded from storage.

    This is a pure data object (DTO) representing the content of the YAML file.
    It does not contain rendering logic.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(
        ...,
        description="Unique identifier for the prompt (e.g., 'sentiment_analysis').",
    )

    version: str = Field(
        ..., description="Semantic version of this template (e.g., '1.0.0')."
    )

    description: Optional[str] = Field(
        default=None, description="Human-readable description of the prompt's purpose."
    )

    template: str = Field(
        ...,
        description="The raw text content containing placeholders (e.g., Jinja2 syntax).",
    )

    input_variables: List[str] = Field(
        default_factory=list,
        description="List of variable names required to render this template.",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata (e.g., tags, author, model configuration suggestions).",
    )
