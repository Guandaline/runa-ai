# src/nala/athomic/observability/tracing/__init__.py
from opentelemetry.trace import SpanKind, StatusCode

from .domain import TraceSource, TraceStatus
from .tracing import (
    Tracer,
    get_current_span,
    get_tracer,
    set_span_status_error,
    set_span_status_ok,
    setup_tracing,
    start_span,
)

__all__ = [
    "get_tracer",
    "get_current_span",
    "setup_tracing",
    "start_span",
    "set_span_status_ok",
    "set_span_status_error",
    "StatusCode",
    "SpanKind",
    "Tracer",
    "TraceStatus",
    "TraceSource",
]
