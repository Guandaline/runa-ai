# src/nala/athomic/observability/metrics/probes/redis_health_probe.py
from prometheus_client import Gauge

from nala.athomic.config import get_settings
from nala.athomic.observability.metrics.protocol import MetricProbe

# Define a global gauge metric exposed by the Prometheus client
redis_available = Gauge("redis_up", "Indicates if Redis is available (1) or not (0).")


class RedisHealthProbe(MetricProbe):
    """
    A specific MetricProbe implementation that checks the connectivity
    and readiness of the configured Redis caching backend.

    The status (1 or 0) is reported to the 'redis_up' Gauge metric.
    """

    name: str = "redis_health_probe"

    async def update(self) -> None:
        """
        Executes the Redis availability check. Sets the gauge to 0 if the
        cache module is disabled, or based on the connection status.
        """
        settings = get_settings().performance.cache

        # Check 1: If the cache module is disabled, report down (0)
        if not settings.enabled:
            redis_available.set(0)
            return

        try:
            # Lazy import to avoid circular dependencies and ensure the module is configured
            from nala.athomic.performance.cache import cache

            # The 'cache' object implements the Protocol with the health check
            redis = cache

            # Delegates the actual health check (e.g., a PING command) to the cache layer
            await redis.is_available()

            # Success
            redis_available.set(1)
        except Exception:
            # Failure (ConnectionError, Timeout, or any other issue)
            redis_available.set(0)
