"""
Prometheus metrics to monitor the lifecycle of stateful services.

These metrics track connection status, attempts, failures and readiness state
of components that inherit from `BaseService`.
"""

from prometheus_client import Counter, Gauge

# Metric for the current connection status of a service.
# Value 1 indicates connected, 0 indicates disconnected.
service_connection_status = Gauge(
    "service_connection_status",
    "Current connection status of a service (1 if connected, 0 otherwise)",
    ["service"],
)

# Metric for the readiness status of a service.
# Value 1 indicates ready, 0 indicates not ready.
service_readiness_status = Gauge(
    "service_readiness_status",
    "Readiness status of a service (1 if ready, 0 otherwise)",
    ["service"],
)

# Total counter of connection attempts.
service_connection_attempts_total = Counter(
    "service_connection_attempts_total",
    "Total number of connection attempts for a service",
    ["service"],
)

# Total counter of connection failures.
service_connection_failures_total = Counter(
    "service_connection_failures_total",
    "Total number of failures when trying to connect a service",
    ["service"],
)
