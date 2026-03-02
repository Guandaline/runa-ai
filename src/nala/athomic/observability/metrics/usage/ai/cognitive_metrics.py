# src/nala/athomic/observability/metrics/usage/ai/cognitive_metrics.py
from prometheus_client import Counter, Histogram

from nala.athomic.observability.metrics.enums import MetricNamespace

_NAMESPACE = MetricNamespace.AI.value
_SUBSYSTEM = "cognitive"

# --- Latency ---
cognitive_classification_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_classification_duration_seconds",
    documentation="Time spent classifying user intent.",
    labelnames=["provider", "strategy"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# --- Throughput & Status ---
cognitive_classification_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_classification_total",
    documentation="Total number of intent classification requests.",
    labelnames=["provider", "strategy", "status"],  # status: success, failure
)

# --- Business Insight: What are users asking? ---
cognitive_intent_detected_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_intent_detected_total",
    documentation="Count of detected intents (e.g., search, tool_use) to analyze user behavior.",
    labelnames=["intent"],
)

# --- Quality: How sure is the model? ---
cognitive_confidence_score = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_confidence_score",
    documentation="Distribution of confidence scores returned by the engine.",
    labelnames=["provider", "strategy"],
    buckets=(0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0),
)
