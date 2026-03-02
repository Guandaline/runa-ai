# Métricas de Retry
from prometheus_client import Counter

retry_attempts_total = Counter(
    "retry_attempts_total", "Total number of retry attempts made", ["operation"]
)

retry_failures_total = Counter(
    "retry_failures_total",
    "Total number of functions that failed after all retries.",
    ["operation"],
)
retry_circuit_breaker_aborts_total = Counter(
    "retry_circuit_breaker_aborts_total",
    "Total retries aborted by the circuit breaker.",
    ["operation"],
)
