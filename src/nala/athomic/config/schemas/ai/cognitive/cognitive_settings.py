# src/nala/athomic/config/schemas/ai/cognitive/cognitive_settings.py
from typing import Optional

from pydantic import BaseModel, Field


class CognitiveSettings(BaseModel):
    """
    Configuration settings for the Cognitive Services (Intent/NLU) domain.

    This configuration drives the CognitiveFactory to select the appropriate
    classification strategy (e.g., LLM-based vs ML-based) and defines
    execution thresholds.
    """

    enabled: bool = Field(
        default=True,
        description="Master switch to enable/disable cognitive intent analysis.",
    )
    strategy: str = Field(
        default="llm",
        description="The strategy backend to use (e.g., 'llm', 'ml_ensemble').",
    )
    default_model: Optional[str] = Field(
        default=None,
        description="Optional model override specifically for cognitive tasks (e.g., 'gpt-4o').",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score required to accept a classification automatically.",
    )
    default_prompt_template: str = Field(
        default="cognitive/intent_classification",
        description="The default Jinja2 template name for LLM-based classification.",
    )
