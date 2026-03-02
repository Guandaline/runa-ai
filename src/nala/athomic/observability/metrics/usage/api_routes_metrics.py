from prometheus_client import Counter, Histogram

api_route_requests_total = Counter(
    "nala_api_route_requests_total",
    "Total number of requests handled by a specific API route.",
    ["route_name", "status"],  # status: success, error, http_error
)

api_route_request_duration_seconds = Histogram(
    "nala_api_route_request_duration_seconds",
    "Duration of requests handled by a specific API route.",
    ["route_name"],
)
