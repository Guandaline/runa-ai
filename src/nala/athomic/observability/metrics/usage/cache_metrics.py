from prometheus_client import Counter

cache_hit_counter = Counter(
    "cache_hits_total", "Total number of cache hits", ["provider"]
)

cache_miss_counter = Counter(
    "cache_misses_total", "Total number of cache misses", ["provider"]
)

cache_error_counter = Counter(
    "cache_errors_total", "Total number of cache errors", ["provider"]
)
cache_stale_hits_total = Counter(
    "nala_cache_stale_hits_total",
    "Total number of times a 'stale' cache value was served while a background update was occurring.",
    ["cache_key_prefix"],
)

cache_background_refreshes_total = Counter(
    "nala_cache_background_refreshes_total",
    "Total number of cache background updates started by the refresh-ahead mechanism.",
    ["cache_key_prefix", "status"],  # status: "success" or "failure"
)
