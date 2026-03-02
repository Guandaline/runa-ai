from typing import List

from pydantic import BaseModel, Field


class ModelRule(BaseModel):
    """
    Defines a context window rule for a specific model or model family.
    Used by the Registry to resolve capabilities dynamically via Regex.
    """

    pattern: str = Field(
        ..., description="Regex pattern to match model names (e.g., '^gpt-4-turbo.*')."
    )
    context_window: int = Field(
        ..., description="Maximum context window size in tokens for matching models."
    )
    encoding_name: str = Field(
        default="cl100k_base",
        description="The tokenizer encoding to use (e.g., 'cl100k_base', 'p50k_base').",
    )


class AIContextSettings(BaseModel):
    """
    Configuration settings for the AI Context Domain (LLM Token Budgeting).

    NOTE: This is distinct from the infrastructure 'ContextSettings' which handles
    request tracing and multi-tenancy. This class specifically handles LLM
    Context Windows, Token Counting rules, and Model limits.
    """

    enabled: bool = True

    # Safety margin to reserve in the context window to prevent overflows.
    # 0.05 means 5% of the total window is kept free.
    default_safety_margin: float = Field(default=0.05, ge=0.0, le=0.5)

    # Fallback values if no rule matches the requested model
    default_model_limit: int = Field(default=4096)
    default_encoding: str = Field(default="cl100k_base")

    # Ordered list of rules. The Registry will use the First Match Wins strategy.
    model_rules: List[ModelRule] = Field(
        default_factory=lambda: [
            # --- OpenAI GPT-4 Families ---
            ModelRule(pattern=r"^gpt-4-(turbo|o|1106|0125).*", context_window=128000),
            ModelRule(pattern=r"^gpt-4-32k.*", context_window=32768),
            ModelRule(pattern=r"^gpt-4.*", context_window=8192),
            # --- OpenAI GPT-3.5 Families ---
            ModelRule(pattern=r"^gpt-3\.5-turbo-16k.*", context_window=16385),
            ModelRule(pattern=r"^gpt-3\.5.*", context_window=4096),
            # --- Anthropic Claude (Generic) ---
            ModelRule(pattern=r"^claude-3.*", context_window=200000),
            ModelRule(pattern=r"^claude-2.*", context_window=100000),
            # --- Open Source / Local Models (Ollama/Groq) ---
            ModelRule(pattern=r"^llama3.*", context_window=8192),  # Default safe limit
            ModelRule(pattern=r"^mistral.*", context_window=32000),
            ModelRule(pattern=r"^mixtral.*", context_window=32000),
            ModelRule(pattern=r"^gemma.*", context_window=8192),
        ],
        description="List of regex rules to resolve model capabilities.",
    )
