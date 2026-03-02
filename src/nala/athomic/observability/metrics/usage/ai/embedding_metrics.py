# src/nala/athomic/observability/metrics/usage/embedding_metrics.py
"""
Defines Prometheus metrics specifically for Embedding operations.
"""

from prometheus_client import Counter, Histogram

embedding_operation_duration_seconds = Histogram(
    "embedding_operation_duration_seconds",
    "Time spent performing embedding operations",
    ["provider", "model", "operation"],  # operation: embed_documents, embed_query
)

embedding_operations_total = Counter(
    "embedding_operations_total",
    "Total number of embedding operations executed",
    ["provider", "model", "operation", "status"],
)

embedding_token_usage_total = Counter(
    "embedding_token_usage_total",
    "Total number of tokens processed for embeddings",
    ["provider", "model"],
)
