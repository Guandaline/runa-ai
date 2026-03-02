# src/nala/athomic/observability/metrics/ai/cache_metrics.py
from prometheus_client import Counter, Histogram

# --- Operation Counters ---

ai_semantic_cache_lookup_total = Counter(
    "ai_semantic_cache_lookup_total",
    "Total number of semantic cache lookup operations.",
    ["status"],  # status: 'hit', 'miss', 'error'
)

ai_semantic_cache_write_total = Counter(
    "ai_semantic_cache_write_total",
    "Total number of semantic cache write (store) operations.",
    ["status"],  # status: 'success', 'failure'
)

# --- Latency Histograms ---

ai_semantic_cache_lookup_duration_seconds = Histogram(
    "ai_semantic_cache_lookup_duration_seconds",
    "Latency of the semantic cache lookup operation (embedding + vector search + kv fetch).",
    ["status"],  # status: 'hit', 'miss'
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# --- Cost Efficiency ---

ai_semantic_cache_saved_tokens_total = Counter(
    "ai_semantic_cache_saved_tokens_total",
    "Total number of tokens (prompt + completion) saved by cache hits.",
    ["model"],
)
