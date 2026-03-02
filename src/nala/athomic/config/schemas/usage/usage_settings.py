from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .aggregation_settings import (
    UsageAggregationSettings,
)
from .emission_settings import UsageEmissionSettings


class UsageSettings(BaseModel):
    """
    Defines the root configuration for the Usage module.

    The Usage module is responsible for modeling and emitting technical
    consumption facts derived from execution signals. It does not implement
    business rules such as billing, pricing, quotas, or tier enforcement.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Master switch to enable or disable the Usage module.",
    )

    strict_mode: bool = Field(
        default=False,
        alias="STRICT_MODE",
        description=(
            "When enabled, internal usage errors are logged as errors instead of warnings. "
            "Execution flow is never interrupted."
        ),
    )

    emit_metrics: bool = Field(
        default=True,
        alias="EMIT_METRICS",
        description="Translate usage events into observability metrics.",
    )

    aggregation: UsageAggregationSettings = Field(
        default_factory=UsageAggregationSettings,
        alias="AGGREGATION",
        description="Settings controlling in-memory aggregation of usage events.",
    )

    emission: Optional[UsageEmissionSettings] = Field(
        default=None,
        alias="EMISSION",
        description="Settings controlling how usage events are emitted.",
    )
