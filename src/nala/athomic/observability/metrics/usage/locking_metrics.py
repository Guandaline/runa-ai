from prometheus_client import Counter, Histogram

locking_attempts_total = Counter(
    "locking_attempts_total",
    "Total number of lock acquisition attempts.",
    ["lock_name", "backend", "status"],
)

locking_hold_duration_seconds = Histogram(
    "locking_hold_duration_seconds",
    "Duration in seconds that a lock is held.",
    ["lock_name", "backend"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, float("inf")),
)
