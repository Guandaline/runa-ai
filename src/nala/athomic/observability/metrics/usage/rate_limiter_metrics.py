from prometheus_client import Counter

rate_limiter_allowed_total = Counter(
    "nala_rate_limiter_allowed_total",
    "Total number of requests allowed by the rate limiter.",
    ["policy", "backend"],  # Labels to filter by policy and provider backend
)

# Counter for requests that were blocked/throttled.
rate_limiter_blocked_total = Counter(
    "nala_rate_limiter_blocked_total",
    "Total number of requests blocked by the rate limiter.",
    ["policy", "backend"],  # Labels to understand which policies are being hit
)
