from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .messaging_metrics_config import MessagingMetricsSettings


class MetricsSettings(BaseModel):
    """Defines the configuration for the Prometheus metrics system.

    This model configures the collection and exposure of Prometheus metrics.
    It controls the master switch for metrics, security for the metrics
    endpoint, and the collection interval for background probes.

    Attributes:
        enabled (Optional[bool]): A master switch for metrics collection.
        allow_metrics_ips (Optional[List[str]]): An IP allowlist for the
            metrics endpoint.
        metrics_protection_enabled (Optional[bool]): Toggles IP protection for
            the metrics endpoint.
        messaging (Optional[MessagingMetricsSettings]): Nested configuration for
            messaging-specific observability.
        collection_interval_seconds (int): The interval for running metric probes.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: Optional[bool] = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to enable or disable the collection and exposure of Prometheus metrics.",
    )

    allow_metrics_ips: Optional[List[str]] = Field(
        default=None,
        description="A list of IP addresses that are allowed to access the internal metrics endpoint (e.g., `/metrics`).",
        alias="ALLOW_METRICS_IPS",
    )

    metrics_protection_enabled: Optional[bool] = Field(
        default=False,
        description="If True, access to the internal metrics endpoint is restricted to the IPs in `allow_metrics_ips`.",
        alias="METRICS_PROTECTION_ENABLED",
    )

    messaging: Optional[MessagingMetricsSettings] = Field(
        default_factory=MessagingMetricsSettings,
        alias="MESSAGING_METRICS",
        description="A nested configuration for fine-grained control over observability within the messaging module.",
    )

    collection_interval_seconds: int = Field(
        default=60,
        ge=1,
        description="The interval in seconds at which the `MetricScheduler` runs its probes to collect gauge-based metrics.",
        alias="COLLECTION_INTERVAL_SECONDS",
    )
