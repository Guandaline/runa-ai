# src/nala/athomic/observability/metrics/enums.py
from enum import Enum


class MetricNamespace(str, Enum):
    """
    Defines high-level namespaces for Prometheus metrics.

    These prefixes are used to namespace metrics by domain, preventing collisions
    and enabling easier aggregation in monitoring dashboards (e.g., Grafana).

    Structure: {namespace}_{subsystem}_{name}_{unit}
    Example: ai_rag_retrieval_duration_seconds
    """

    ATHOMIC = "athomic"  # Core framework metrics (system, lifecycle)
    AI = "ai"  # AI Foundation (LLM, RAG, Agents)
    QUALITY = (
        "quality"  # AI Quality Assurance (Faithfulness, Accuracy, Semantic Scores)
    )
    DATABASE = "db"  # Persistence (Vector, Mongo, KV, Graph)
    SECURITY = "sec"  # Security (Auth, Secrets, Crypto)
    MESSAGING = "msg"  # Integration (Kafka, Outbox)
    HTTP = "http"  # Networking (HTTP Clients)
    RESILIENCE = "res"  # Reliability patterns (Circuit Breaker, Rate Limit)

    def __str__(self) -> str:
        return self.value


class MetricStatus(str, Enum):
    """
    Defines standardized values for the 'status' label in Prometheus metrics
    across the application (e.g., success rate, caching results).
    """

    SUCCESS = "success"
    FAILURE = "failure"
    MISS = "miss"
    HIT = "hit"
    ERROR = "error"  # Explicit error (unexpected exception)
    DROPPED = "dropped"  # Dropped due to rate limiting or queue overflow

    def __str__(self) -> str:
        return self.value


class DbOperation(str, Enum):
    """
    Defines standardized operation names for database and KVStore metrics
    and tracing spans, ensuring consistency across persistence layers.
    """

    SAVE = "save"
    GET = "get"
    SET = "set"
    DELETE = "delete"
    FIND_ALL = "find_all"
    FIND_BY_ID = "find_by_id"
    FIND_BY_OWNER = "find_by_owner"
    EXISTS = "exists"
    CLEAR = "clear"
    IS_AVAILABLE = "is_available"

    # Specific operations for sorted sets (e.g., Redis/KVStore usage)
    ZADD = "zadd"
    ZREM = "zrem"
    ZPOPBYSCORE = "zpopbyscore"
    ZRANGEBYSCORE = "zrangebyscore"

    # Specific operations for Hash maps
    HSET = "hset"
    HGETALL = "hgetall"
    HDEL = "hdel"

    def __str__(self) -> str:
        return self.value


class FallbackReadStrategyType(str, Enum):
    """
    Defines standardized read strategies for the resilient FallbackKVProvider.
    These values determine when the provider attempts to read from the
    secondary (fallback) cache layer.
    """

    ON_ERROR = "on_error"
    ON_MISS_OR_ERROR = "on_miss_or_error"

    def __str__(self) -> str:
        return self.value


class FallbackWriteStrategyType(str, Enum):
    """
    Defines standardized write strategies for the resilient FallbackKVProvider.
    These values determine how data is written to the primary and secondary
    (fallback) cache layers.
    """

    WRITE_AROUND = "write_around"
    WRITE_THROUGH = "write_through"

    def __str__(self) -> str:
        return self.value
