# src/nala/athomic/observability/metrics/usage/llm_metrics.py
"""
Defines Prometheus metrics for Large Language Models (LLM) usage.
Captures latency, throughput, and token consumption.
"""

from prometheus_client import Counter, Histogram

llm_operation_duration_seconds = Histogram(
    "llm_operation_duration_seconds",
    "Time spent performing LLM operations",
    ["provider", "model", "operation"],
)

llm_operations_total = Counter(
    "llm_operations_total",
    "Total number of LLM operations executed",
    ["provider", "model", "operation", "status"],
)

llm_token_usage_total = Counter(
    "llm_token_usage_total",
    "Total number of tokens processed/generated",
    ["provider", "model", "token_type"],
)
