# src/nala/athomic/observability/metrics/usage/ai/workflow_metrics.py
"""
Defines Prometheus metrics for the Workflow Orchestration Engine.
Captures end-to-end execution latency, step-level performance, and error rates.
"""

from prometheus_client import Counter, Histogram

from nala.athomic.observability.metrics.enums import MetricNamespace

_NAMESPACE = MetricNamespace.AI.value
_SUBSYSTEM = "workflow"

# --- High-Level Workflow Metrics ---

workflow_execution_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_execution_duration_seconds",
    documentation="Time spent executing the full workflow from start to finish.",
    labelnames=["workflow_name", "status"],  # status: success, failure
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

workflow_executions_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_executions_total",
    documentation="Total number of workflow executions triggered.",
    labelnames=["workflow_name", "status"],
)

workflow_steps_count = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_steps_count",
    documentation="Number of steps (nodes) visited during a workflow execution.",
    labelnames=["workflow_name"],
    buckets=(1, 5, 10, 20, 50, 100),
)

# --- Granular Node Metrics ---

workflow_step_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_step_duration_seconds",
    documentation="Time spent executing a single node/step within a workflow.",
    labelnames=["workflow_name", "step_name", "status"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
)

workflow_step_errors_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_step_errors_total",
    documentation="Total number of errors encountered at the step level.",
    labelnames=["workflow_name", "step_name", "error_type"],
)
