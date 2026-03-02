# src/nala/athomic/observability/tracing/setup.py
from typing import Any, Dict, Optional

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

from nala.athomic.config import get_settings
from nala.athomic.config.schemas import ObservabilitySettings
from nala.athomic.config.schemas.app_settings import AppSettings
from nala.athomic.context.context_vars import get_request_id, get_trace_id

_tracing_initialized = False


def setup_tracing(settings: Optional[AppSettings] = None) -> None:
    """
    Initializes the OpenTelemetry Tracing SDK, configures the OTLP exporter,
    and instruments core libraries.

    This function is idempotent and serves as the central configuration point
    for distributed tracing.
    """
    global _tracing_initialized
    if _tracing_initialized:
        logger.debug("OpenTelemetry Tracing already initialized.")
        return

    try:
        settings: AppSettings = settings or get_settings()
        obs_settings: Optional[ObservabilitySettings] = settings.observability
    except Exception as e:
        logger.error(f"Failed to load settings for tracing configuration: {e}")
        obs_settings = None

    # Circuit Breaker: Check enablement
    if not obs_settings or not obs_settings.enabled or not obs_settings.tracing_enabled:
        logger.info("OpenTelemetry Tracing is disabled in the configuration.")
        _tracing_initialized = True
        return

    # --- 1. Exporter Setup (Conditional) ---
    exporter = None
    if not obs_settings.otlp_endpoint:
        logger.warning(
            "OTLP endpoint not configured (OBSERVABILITY__OTLP_ENDPOINT). "
            "Tracing SDK initialized, but spans will not be exported."
        )
    else:
        logger.info(
            f"Configuring OTLP Exporter for: {obs_settings.otlp_endpoint} (Protocol: {obs_settings.otlp_protocol})"
        )
        exporter = OTLPSpanExporter(
            endpoint=obs_settings.otlp_endpoint,
            insecure=True,  # Note: insecure should be set to False for production with TLS
            headers=obs_settings.otlp_headers,
        )

    # --- 2. Resource (Service Name) Setup ---
    service_name = obs_settings.service_name_override or settings.app_name or "athomic"
    resource = Resource(attributes={SERVICE_NAME: service_name})
    logger.info(f"Setting OpenTelemetry service name to: '{service_name}'")

    # --- 3. Sampling Setup ---
    try:
        sampling_rate = float(obs_settings.sampling_rate)
        sampler = TraceIdRatioBased(sampling_rate)
        logger.info(f"Setting OpenTelemetry sampling rate to: {sampling_rate}")
    except ValueError:
        logger.error(
            f"Invalid value for sampling_rate: '{obs_settings.sampling_rate}'. Using default 1.0."
        )
        sampler = TraceIdRatioBased(1.0)

    # --- 4. TracerProvider and SpanProcessor Setup ---
    provider = TracerProvider(resource=resource, sampler=sampler)
    if exporter:
        # Use BatchSpanProcessor for efficiency (sends spans in batches)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logger.info("OTLP Span Exporter added to TracerProvider.")
    else:
        logger.warning(
            "No OTLP exporter configured, spans will not be sent to a backend."
        )

    # Set the configured provider as the global instance
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry TracerProvider set as global.")

    # --- 5. Auto-Instrumentation ---
    logger.info("Instrumenting libraries for OpenTelemetry...")
    try:
        LoggingInstrumentor().instrument(set_logging_format=False)
        logger.debug("Logging instrumented.")
        RequestsInstrumentor().instrument()
        logger.debug("Requests instrumented.")
        PymongoInstrumentor().instrument()
        logger.debug("PyMongo instrumented.")
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumented.")
    except Exception as e:
        logger.error(f"Failed to instrument libraries: {e}")

    _tracing_initialized = True
    logger.success("OpenTelemetry Tracing SDK and instrumentors configured.")


def get_tracer(name: Optional[str] = None) -> Tracer:
    """
    Retrieves the global OpenTelemetry Tracer instance, optionally scoped by name.

    Args:
        name: The name used to scope the tracer instance. Defaults to the
              configured service name.
    """
    effective_name = name
    if not effective_name:
        try:
            settings = get_settings()
            obs_settings = settings.observability
            effective_name = (
                (obs_settings.service_name_override if obs_settings else None)
                or settings.app_name
                or "athomic"
            )
        except Exception:
            effective_name = "athomic"

    # Delegates to the global OpenTelemetry method
    return trace.get_tracer(effective_name)


def start_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
) -> trace.Span:
    """
    Starts a new trace span, injecting custom Athomic context attributes
    (request.id, trace.id) into the span before execution.

    Args:
        name: The name of the span.
        kind: The SpanKind (e.g., SERVER, CLIENT, CONSUMER).
        attributes: Additional span attributes.

    Returns:
        trace.Span: The newly created span instance.
    """
    tracer = get_tracer()
    ctx_attributes: Dict[str, Any] = {}

    # Inject Athomic context variables into the span attributes
    try:
        req_id = get_request_id()
        trace_id = get_trace_id()
        if req_id:
            ctx_attributes["request.id"] = req_id
        if trace_id:
            # Note: trace.id is usually handled by OpenTelemetry, this is for explicit logging/context
            ctx_attributes["trace.id.explicit"] = trace_id
    except LookupError:
        logger.trace(
            "Context variables (request_id, trace_id) not found for span attributes."
        )
    except Exception as e:
        logger.warning(
            f"Could not retrieve request/trace context for span attributes: {e}"
        )

    if attributes:
        ctx_attributes.update(attributes)

    # Filter out None values
    final_attributes = {
        k: v for k, v in ctx_attributes.items() if v is not None
    } or None

    span = tracer.start_span(name=name, kind=kind, attributes=final_attributes)
    return span


def set_span_status_ok(span: Span, message: str = "OK") -> None:
    """Sets the span status to OK."""
    span.set_status(Status(StatusCode.OK, message))


def set_span_status_error(
    span: Span, message: str, record_exception: bool = True
) -> None:
    """Sets the span status to ERROR and optionally records an exception."""
    if record_exception:
        # Note: None is passed as exception object if not provided by caller
        span.record_exception(None)
    span.set_status(Status(StatusCode.ERROR, message))


def get_current_span() -> Span:
    """
    Returns the active span in the current execution context.

    This acts as a wrapper over the direct OpenTelemetry call to maintain
    abstraction within the Athomic engine.
    """
    return trace.get_current_span()
