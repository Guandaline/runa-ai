# src/nala/athomic/resilience/rate_limiter/registry.py
from typing import Type

from nala.athomic.base import BaseRegistry
from nala.athomic.resilience.rate_limiter.protocol import RateLimiterProtocol
from nala.athomic.resilience.rate_limiter.providers import (
    LimitsRateLimiter,
    RedisRateLimiter,
)


class RateLimiterRegistry(BaseRegistry[Type[RateLimiterProtocol]]):
    """
    Registry for RateLimiterProtocol implementations.
    Maps backend names to their corresponding provider classes.
    """

    def register_defaults(self) -> None:
        """
        Registers the default rate limiter providers.
        This method is called automatically by the BaseRegistry constructor.
        """
        self.register("limits", LimitsRateLimiter)
        self.register("redis", RedisRateLimiter)


rate_limiter_registry = RateLimiterRegistry(protocol=RateLimiterProtocol)
