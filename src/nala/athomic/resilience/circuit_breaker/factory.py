# src/nala/athomic/resilience/circuit_breaker/factory.py
from typing import Optional

from nala.athomic.config.schemas.resilience.circuit_breaker.circuit_breaker_config import (
    CircuitBreakerSettings,
)
from nala.athomic.config.settings import get_settings
from nala.athomic.observability.log import get_logger

from .service import CircuitBreakerService

logger = get_logger(__name__)


class CircuitBreakerFactory:
    """
    Factory to create and manage the singleton instance of CircuitBreakerService.
    """

    _instance: Optional[CircuitBreakerService] = None

    @classmethod
    def create(
        cls,
        settings: Optional[CircuitBreakerSettings] = None,
    ) -> CircuitBreakerService:
        """
        Creates or returns the singleton instance of the CircuitBreakerService.
        """
        if not settings:
            logger.info("CircuitBreakerSettings not provided, using default settings.")
            settings = get_settings().resilience.circuit_breaker

        if cls._instance is None:
            logger.debug("Creating new CircuitBreakerService singleton instance.")
            cls._instance = CircuitBreakerService(settings=settings)
        else:
            logger.debug("Returning cached CircuitBreakerService singleton instance.")
        return cls._instance

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the cached singleton instance. Useful for tests."""
        cls._instance = None
        logger.info("CircuitBreakerFactory cache cleared.")
