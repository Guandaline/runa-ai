# config/schemas/observability/observability_config.py
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.observability.metrics.metrics_config import (
    MetricsSettings,
)


class ObservabilitySettings(BaseModel):
    """Defines the configuration for the observability stack (Metrics and Tracing).

    This model configures the collection and export of telemetry data. It controls
    the Prometheus metrics exporter, the OpenTelemetry (OTLP) trace exporter,
    and includes nested settings for more fine-grained control over metrics.

    Attributes:
        enabled (bool): A master switch for all observability features.
        exporter_enabled (bool): Toggles the Prometheus metrics HTTP server.
        exporter_port (int): The port for the Prometheus metrics server.
        tracing_enabled (bool): A master switch for distributed tracing.
        otlp_endpoint (Optional[str]): The endpoint for the OpenTelemetry Collector.
        otlp_protocol (Literal["grpc", "http/protobuf"]): The OTLP export protocol.
        otlp_headers (Optional[Dict[str, str]]): Headers for the OTLP exporter.
        service_name_override (Optional[str]): Overrides the default service name
            in traces.
        sampling_rate (float): The sampling rate for traces (0.0 to 1.0).
        metrics (Optional[MetricsSettings]): Nested configuration for specific
            metrics settings.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to globally enable or disable all observability features (metrics and tracing).",
    )

    exporter_enabled: bool = Field(
        default=True,
        description="If True, starts an HTTP server to expose Prometheus metrics on the `/metrics` endpoint.",
    )
    exporter_port: int = Field(
        default=9100,
        description="The port on which the Prometheus metrics server will listen.",
    )

    tracing_enabled: bool = Field(
        default=True,
        description="A master switch to enable or disable the collection and export of OpenTelemetry traces.",
    )
    otlp_endpoint: Optional[str] = Field(
        default=None,
        description="The gRPC or HTTP endpoint of the OpenTelemetry Collector where traces will be sent.",
    )
    otlp_protocol: Literal["grpc", "http/protobuf"] = Field(
        default="grpc",
        description="The protocol to be used for exporting OTLP traces.",
    )
    otlp_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="A dictionary of additional headers to be sent with OTLP trace exports (e.g., for authentication).",
    )
    service_name_override: Optional[str] = Field(
        default=None,
        description="An optional name to override the default application name for the 'service.name' attribute in traces.",
    )
    sampling_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="The sampling rate for traces, expressed as a float between 0.0 (sample none) and 1.0 (sample all).",
    )

    metrics: Optional[MetricsSettings] = Field(
        default_factory=MetricsSettings,
        alias="METRICS",
        description="A nested configuration for more specific metrics settings, such as security and collection intervals.",
    )
