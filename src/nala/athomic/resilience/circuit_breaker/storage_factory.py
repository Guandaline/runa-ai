# src/nala/athomic/resilience/circuit_breaker/storage_factory.py
import asyncio

import redis as sync_redis
from aiobreaker.state import CircuitBreakerState
from aiobreaker.storage.base import CircuitBreakerStorage
from aiobreaker.storage.memory import CircuitMemoryStorage

from nala.athomic.config.schemas.resilience import CircuitBreakerSettings
from nala.athomic.observability import get_logger

from .patched_storage import PatchedCircuitRedisStorage

logger = get_logger(__name__)


class CircuitBreakerStorageFactory:
    """
    Factory responsible for asynchronously creating and configuring the storage
    backend for a `CircuitBreaker` instance.

    It supports two main types of storage: Redis (for distributed state) and
    in-memory (for local development/single-instance applications).
    """

    @classmethod
    async def create(
        cls, circuit_name: str, settings: CircuitBreakerSettings
    ) -> CircuitBreakerStorage:
        """
        Creates the appropriate storage provider for the circuit breaker based on settings.

        Prioritizes Redis storage for distributed state. If Redis is not configured,
        fails to connect, or is explicitly disabled, it falls back to in-memory storage.

        Args:
            circuit_name (str): The unique name of the circuit being configured.
            settings (CircuitBreakerSettings): The application's circuit breaker configuration.

        Returns:
            CircuitBreakerStorage: A configured storage instance (Redis or in-memory).

        Raises:
            ValueError: If Redis is configured but the connection URI is missing.
        """
        storage_config = settings.provider

        # Check for Redis backend configuration
        if not storage_config or storage_config.backend != "redis":
            logger.warning(
                f"Using in-memory storage for circuit '{circuit_name}'. State will be lost on restart."
            )
            return CircuitMemoryStorage(state=CircuitBreakerState.CLOSED)

        logger.debug(f"Creating Redis storage for circuit '{circuit_name}'.")
        try:
            redis_uri_secret = storage_config.redis.uri

            if not redis_uri_secret:
                raise ValueError(
                    "Redis URI for Circuit Breaker storage is not configured."
                )

            # Resolve the secret to a string value
            redis_uri_str = redis_uri_secret.get_secret_value()

            # Create a synchronous Redis client instance
            redis_client = sync_redis.from_url(redis_uri_str)

            # Verify connectivity asynchronously using asyncio.to_thread
            await asyncio.to_thread(redis_client.ping)

            # Use the patched Redis storage that supports unique naming/namespace isolation
            return PatchedCircuitRedisStorage(
                circuit_name=circuit_name,
                initial_state=CircuitBreakerState.CLOSED,
                redis_object=redis_client,
                namespace=settings.namespace,
            )
        except Exception:
            logger.exception(
                "Failed to create Redis circuit breaker storage. Falling back to in-memory."
            )
            return CircuitMemoryStorage(state=CircuitBreakerState.CLOSED)
