from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class PIIPattern(BaseModel):
    """Defines a single PII regex pattern and its replacement string."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    regex: str = Field(
        ..., description="The regular expression to detect the PII type."
    )
    replacement: str = Field(
        "***PII_REDACTED***", description="The string used to replace the detected PII."
    )


class PIISanitizerSettings(BaseModel):
    """Configuration for the PII Sanitization Guardrail."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="Master switch to enable PII detection and sanitization.",
    )

    patterns: Dict[str, PIIPattern] = Field(
        default_factory=lambda: {
            "EMAIL": PIIPattern(
                regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            ),
            "PHONE": PIIPattern(regex=r"(\(?\d{2}\)?\s)?(\d{4,5}[-\s]?\d{4})"),
            "CPF": PIIPattern(regex=r"\d{3}\.\d{3}\.\d{3}-\d{2}"),
            "CREDIT_CARD": PIIPattern(regex=r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
        },
        description="Named list of regular expressions used for PII detection.",
    )


class KeywordBlocklistSettings(BaseModel):
    """Configuration for the Keyword/Topic Blocklist Guardrail."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    enabled: bool = Field(
        default=True, description="Master switch to enable keyword blocking."
    )
    blocklist: List[str] = Field(
        default_factory=list, description="List of forbidden words."
    )


class GovernanceRateLimitSettings(BaseModel):
    """Configuration for AI-specific Rate Limiting."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    enabled: bool = Field(
        default=True, description="Master switch to enable rate limiting."
    )


class PipelineSettings(BaseModel):
    """
    Configuration for the execution behavior of the GuardPipeline.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    fail_fast: bool = Field(
        default=True,
        description="If True, stops at the first violation. If False, executes all input guards and aggregates errors.",
    )
    continue_on_output_error: bool = Field(
        default=False,
        description="If True, returns the original response if an output guard fails (crashes), logging the error.",
    )


class GovernanceSettings(BaseModel):
    """Top-level configuration for the AI Governance module (Guardrails)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True, description="Master switch to enable all AI governance features."
    )

    pipeline: PipelineSettings = Field(
        default_factory=PipelineSettings,
        description="Settings controlling the execution flow of the guardrails.",
    )

    pii_sanitizer: PIISanitizerSettings = Field(default_factory=PIISanitizerSettings)
    keyword_blocklist: KeywordBlocklistSettings = Field(
        default_factory=KeywordBlocklistSettings
    )
    rate_limiter: GovernanceRateLimitSettings = Field(
        default_factory=GovernanceRateLimitSettings
    )
