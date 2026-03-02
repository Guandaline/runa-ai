# src/nala/athomic/observability/metrics/ai/agent_metrics.py
from prometheus_client import Counter, Histogram

# --- Persistence Metrics ---

agent_checkpoint_operations_total = Counter(
    "agent_checkpoint_operations_total",
    "Total number of agent checkpoint operations (save/load).",
    ["operation", "status", "backend"],  # operation: save/load, status: success/error
)

agent_checkpoint_duration_seconds = Histogram(
    "agent_checkpoint_duration_seconds",
    "Latency of agent checkpoint operations.",
    ["operation", "backend"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

agent_checkpoint_size_bytes = Histogram(
    "agent_checkpoint_size_bytes",
    "Size of the serialized agent state in bytes.",
    ["backend"],
    buckets=(1024, 4096, 16384, 65536, 262144, 1048576),  # 1KB to 1MB+
)

# --- Execution Metrics (Placeholder for future Agent Runtime) ---
# agent_execution_total = Counter(...)
# agent_step_duration_seconds = Histogram(...)
