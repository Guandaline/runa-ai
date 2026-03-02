# src/nala/athomic/resilience/rate_limiter/factory.py
from typing import Optional

from nala.athomic.config import RateLimiterSettings, get_settings
from nala.athomic.observability.log import get_logger
from nala.athomic.resilience.rate_limiter.registry import rate_limiter_registry

from .base import RateLimiterBase

logger = get_logger(__name__)


class RateLimiterFactory:
    """
    Factory responsible for creating the singleton instance of the
    configured rate limiter provider.

    This factory follows the singleton pattern, ensuring that only one
    instance of the rate limiter provider is created and reused throughout
    the application's lifecycle, unless explicitly told otherwise.
    """

    @classmethod
    def create(cls, settings: Optional[RateLimiterSettings] = None) -> RateLimiterBase:
        """
        Creates or returns the singleton instance of a rate limiter provider.

        On the first call, it instantiates the provider based on global or
        injected settings. Subsequent calls return the cached instance.

        Args:
            settings: Optional RateLimiterSettings to use. If None, global
                      settings are fetched. Primarily for testing.

        Returns:
            An instance implementing the RateLimiterProtocol.

        Raises:
            RuntimeError: If rate limiter configuration is missing or disabled.
            ValueError: If the configured backend is not found in the registry.
            ProviderInitializationError: If the provider fails to instantiate.
        """

        if not settings:
            logger.debug("No settings provided, using global settings.")
            settings = get_settings().resilience.rate_limiter

        if not settings or not settings.enabled:
            raise RuntimeError("Rate limiter is not configured or disabled.")

        effective_settings: RateLimiterSettings = settings

        logger.debug(
            f"Creating RateLimiterProvider with settings: {effective_settings}"
        )

        backend_name = effective_settings.backend.lower()
        provider_class = rate_limiter_registry.get(backend_name)

        if not provider_class:
            raise ValueError(f"No provider for backend: '{backend_name}'")

        instance = provider_class(settings=effective_settings)

        return instance
