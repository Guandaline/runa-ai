from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessagingMetricsSettings(BaseModel):
    """Defines observability settings specific to the messaging module.

    This model provides granular control over the metrics and traces emitted
    by messaging components like producers and consumers.

    Attributes:
        enable_metrics (bool): Toggles the collection of Prometheus metrics
            for messaging operations.
        enable_tracing (bool): Toggles the creation of OpenTelemetry traces
            for messaging operations.
        track_consumer_factory (Optional[bool]): Toggles a specific metric
            for tracking consumer creation.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enable_metrics: bool = Field(
        default=True,
        description="If True, enables Prometheus metrics for messaging operations (e.g., messages processed, publish latency).",
    )
    enable_tracing: bool = Field(
        default=True,
        description="If True, enables OpenTelemetry traces for messaging operations.",
    )
    track_consumer_factory: Optional[bool] = Field(
        default=False,
        description="If True, tracks a metric for each consumer registered by the factory, used for internal monitoring.",
    )
