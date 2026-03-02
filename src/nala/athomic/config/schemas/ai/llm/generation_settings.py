# src/nala/athomic/config/schemas/ai/generation_settings.py
"""
Defines the Pydantic schemas for LLM (Large Language Model) generation settings.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerationSettings(BaseModel):
    """
    Defines the default inference parameters for text generation.

    This schema centralizes "magic numbers" related to LLM generation, allowing
    different behavior (e.g., "creative" vs "deterministic") to be configured
    per connection without changing the application code.

    Attributes:
        temperature (float): Controls the randomness of the output.
            Values range from 0.0 (deterministic) to 2.0 (highly random).
        max_output_tokens (int): The maximum number of tokens to generate in the response.
        top_p (float): Nucleus sampling parameter.
            The model considers the results of the tokens with top_p probability mass.
        top_k (Optional[int]): Top-k sampling parameter.
            The model limits the next token selection to the k most likely tokens.
        stop_sequences (Optional[List[str]]): A list of strings that, if generated,
            will stop the generation process.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        alias="TEMPERATURE",
        description="Controls randomness: 0.0 is deterministic, higher values (e.g., 0.9) are more creative.",
    )

    max_output_tokens: int = Field(
        default=8192,
        gt=0,
        alias="MAX_OUTPUT_TOKENS",
        description="The maximum number of tokens the model can generate in a single response.",
    )

    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        alias="TOP_P",
        description="Nucleus sampling: considers the smallest set of tokens whose cumulative probability is at least top_p.",
    )

    top_k: Optional[int] = Field(
        default=40,
        gt=0,
        alias="TOP_K",
        description="Top-k sampling: limits the next token selection to the k most likely tokens.",
    )

    stop_sequences: Optional[List[str]] = Field(
        default=None,
        alias="STOP_SEQUENCES",
        description="A list of specific sequences that will stop the generation if produced.",
    )
