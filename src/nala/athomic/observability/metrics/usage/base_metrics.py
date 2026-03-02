from prometheus_client import Counter, Gauge, Histogram

request_counter = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
)
request_duration = Histogram(
    "api_request_duration_seconds",
    "Duration of API requests in seconds",
    ["method", "endpoint"],
)
in_progress_requests = Gauge(
    "api_requests_in_progress", "Number of in-progress API requests"
)
