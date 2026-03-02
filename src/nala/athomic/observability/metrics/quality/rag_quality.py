# src/nala/athomic/observability/metrics/quality/rag_quality.py
from prometheus_client import Counter, Gauge, Histogram

from nala.athomic.observability.metrics.enums import MetricNamespace

_NAMESPACE = MetricNamespace.QUALITY.value
_SUBSYSTEM = "rag"

# Standard labels for slicing quality metrics.
# model_used: The identifier of the System Under Test (SUT) (e.g., 'gpt-4', 'vertex-gemini').
_LABELS = ["dataset", "metric_name", "model_used"]


# Gauge: The most recent score obtained in a QA evaluation.
# Usage: "Current Status" dashboards. Shows the health of the latest regression run per model.
rag_quality_last_score = Gauge(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_last_score",
    documentation="The most recent score obtained in a QA evaluation run.",
    labelnames=_LABELS,
)

# Histogram: Historical distribution of quality scores.
# Usage: Detecting drift over time. Are we consistently hitting >0.8, or is variance increasing?
rag_quality_score_distribution = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_score_history",
    documentation="Historical distribution of quality scores over time.",
    labelnames=_LABELS,
    # Buckets optimized for quality scores (0.0 to 1.0) with higher granularity at the top end
    buckets=(0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 1.0),
)

# Counter: Total number of test cases that failed (score < threshold).
# Usage: CI/CD Gating. If this increases during a PR build, block the merge.
rag_quality_failures_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_failures_total",
    documentation="Total number of test cases that failed (score below threshold).",
    labelnames=_LABELS,
)

# Counter: Token usage specifically for the Evaluation process (LLM-as-a-Judge).
# Usage: Cost control. Distinguishes 'production tokens' from 'testing tokens'.
rag_evaluation_token_usage_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_evaluation_tokens_total",
    documentation="Total tokens consumed by the evaluation judges (LLM-as-a-Judge).",
    labelnames=[
        "dataset",
        "judge_model",
        "token_type",
    ],  # token_type: prompt, completion
)

# Histogram: Duration of the evaluation logic itself.
# Usage: Monitoring the performance of the QA Harness.
rag_evaluation_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_evaluation_duration_seconds",
    documentation="Time taken to calculate quality metrics for a single case.",
    labelnames=["metric_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)
