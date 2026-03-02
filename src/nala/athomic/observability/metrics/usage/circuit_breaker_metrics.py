# src/nala/athomic/observability/metrics/usage/circuit_breaker_metrics.py
from prometheus_client import Counter, Gauge

# 0: CLOSED, 1: OPEN, 2: HALF_OPEN
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Current state of a circuit breaker (0: closed, 1: open, 2: half-open)",
    ["circuit_name"],
)

circuit_breaker_state_changes_total = Counter(
    "circuit_breaker_state_changes_total",
    "Total number of circuit breaker state changes",
    ["circuit_name", "from_state", "to_state"],
)

circuit_breaker_calls_blocked_total = Counter(
    "circuit_breaker_calls_blocked_total",
    "Total number of calls blocked by an open circuit breaker",
    ["circuit_name"],
)

circuit_breaker_failures_recorded_total = Counter(
    "circuit_breaker_failures_recorded_total",
    "Total number of failures recorded by a circuit breaker",
    ["circuit_name"],
)
