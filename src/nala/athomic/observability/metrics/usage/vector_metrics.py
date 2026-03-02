# src/nala/athomic/observability/metrics/usage/vector_metrics.py
"""
Defines Prometheus metrics for Vector Database operations.
"""

from prometheus_client import Counter, Histogram

# Latency histogram for vector DB operations
vector_db_operation_duration_seconds = Histogram(
    "vector_db_operation_duration_seconds",
    "Time spent performing vector database operations",
    ["backend", "collection", "operation"],  # e.g., qdrant, knowledge_base, search
)

# Counter for operation throughput and status
vector_db_operations_total = Counter(
    "vector_db_operations_total",
    "Total number of vector database operations executed",
    ["backend", "collection", "operation", "status"],
)
