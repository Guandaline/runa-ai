"""
Prometheus metrics to monitor the usage and performance of database.
"""

from prometheus_client import Counter, Histogram

# Counter for the total number of operations, segmented by status (success, error, hit, miss)
kvstore_operations_total = Counter(
    name="kvstore_operations_total",
    documentation="Total number of KV store operations.",
    labelnames=["service_name", "operation", "status"],
)

# Histogram to measure the latency (duration) of operations
kvstore_operation_duration_seconds = Histogram(
    name="kvstore_operation_duration_seconds",
    documentation="Duration of KV store operations in seconds.",
    labelnames=["service_name", "operation"],
)
