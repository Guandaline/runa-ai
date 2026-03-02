# src/nala/athomic/ai/schemas/cognitive.py
import json
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class UserIntent(str, Enum):
    """
    Enumeration of recognized user intents within the system.
    Acts as the primary label for the Intent Engine.
    """

    SEARCH = "search"
    ASK = "ask"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    PLAN = "plan"
    TOOL_USE = "tool_use"
    UNKNOWN = "unknown"


class IntentClassification(BaseModel):
    """
    Structured representation of the user's intent.
    Includes validators to handle loose typing from smaller LLMs.
    """

    primary_intent: UserIntent = Field(
        ...,
        description="The classification of the user's main goal.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0.0 to 1.0).",
    )
    detected_entities: List[str] = Field(
        default_factory=list,
        description="Key entities extracted from the query.",
    )
    rewritten_query: Optional[str] = Field(
        default=None,
        description="Optimized version of the query.",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Flag indicating if the action requires user approval.",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Brief explanation of why this intent was selected.",
    )

    # --- Robustness Validators (Coercion) ---

    @field_validator("primary_intent", mode="before")
    @classmethod
    def normalize_intent(cls, v: Any) -> Any:
        """Handle case insensitivity."""
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_float(cls, v: Any) -> float:
        """Handle stringified floats from LLMs."""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return 0.0
        return v

    @field_validator("requires_confirmation", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        """Handle stringified booleans."""
        if isinstance(v, str):
            return v.lower() == "true"
        return v

    @field_validator("detected_entities", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> List[str]:
        """Handle stringified lists or single items."""
        if isinstance(v, str):
            # Try to parse string representation of list "['a']"
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # If not a JSON list, treat as single item if not empty array string
            if v == "[]":
                return []
            return [v]
        return v

    @field_validator("reasoning", mode="before")
    @classmethod
    def normalize_reasoning(cls, v: Any) -> Optional[str]:
        """Join lists into a single string."""
        if isinstance(v, list):
            return " ".join([str(item) for item in v])
        return v
