from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.resilience.rate_limiter.rate_limiter_config import (
    RateLimiterSettings,
)
from nala.athomic.context import ContextKeyGenerator
from nala.athomic.observability.metrics.usage import (
    rate_limiter_allowed_total,
    rate_limiter_blocked_total,
)
from nala.athomic.observability.tracing import SpanKind, StatusCode
from nala.athomic.services.base import BaseService

from .factory import RateLimiterFactory
from .protocol import RateLimiterProtocol


class RateLimiterService(BaseService):
    """
    Orchestrates rate limiting logic, integrating provider, configuration,
    key generation, and detailed observability.
    """

    def __init__(
        self,
        settings: Optional[RateLimiterSettings] = None,
        provider: Optional[RateLimiterProtocol] = None,
    ):
        """
        Initializes the RateLimiterService.

        Args:
            provider: Allows injecting a specific provider, primarily for testing.
                      If None, the default provider is created via the factory.
        """
        super().__init__(service_name="rate_limiter_service", enabled=True)

        self.settings = settings or get_settings().resilience.rate_limiter
        self.logger.debug(
            f"RateLimiterService initialized with settings: {self.settings}"
        )
        self.provider = provider or RateLimiterFactory.create(settings=self.settings)
        self.logger.debug(
            f"RateLimiterProvider initialized: {self.provider.service_name}"
        )
        self.key_resolver = ContextKeyGenerator(namespace=self.settings.namespace)

    async def check(self, policy: str, *key_parts: str) -> bool:
        """
        Performs a rate limit check with integrated, detailed observability.

        Args:
            policy: The name of the rate limit policy to apply.
            *key_parts: Logical parts of the key (e.g., function name, resource ID).

        Returns:
            True if the request is allowed, False if it is blocked.
        """
        if not self.settings.enabled:
            return True

        backend_name = getattr(self.provider, "service_name", "unknown")

        limit_string = self.settings.policies.get(
            policy, self.settings.default_policy_limit
        )

        if not limit_string or limit_string.lower() == "nolimit":
            return True

        resolved_key = self.key_resolver.generate(policy, *key_parts)

        with self.tracer.start_as_current_span(
            "RateLimiterService.check",
            kind=SpanKind.INTERNAL,
            attributes={
                "ratelimit.policy": policy,
                "ratelimit.limit": limit_string,
                "ratelimit.key": resolved_key,
                "ratelimit.backend": backend_name,
            },
        ) as span:
            is_allowed = await self.provider.allow(resolved_key, limit_string, policy)

            span.set_attribute("ratelimit.allowed", is_allowed)

            if is_allowed:
                rate_limiter_allowed_total.labels(
                    policy=policy, backend=backend_name
                ).inc()
                span.set_status(StatusCode.OK, "Request allowed")
                self.logger.trace(f"Rate limit allowed for key '{resolved_key}'")
            else:
                rate_limiter_blocked_total.labels(
                    policy=policy, backend=backend_name
                ).inc()
                span.set_status(StatusCode.ERROR, "Request blocked by rate limit")
                self.logger.warning(
                    f"Rate limit BLOCKED for key '{resolved_key}' with policy '{policy}' ({limit_string})"
                )

            return is_allowed

    def _connect(self):
        """Establishes connection to the rate limiter backend if needed."""
        pass

    def _close(self):
        """Closes connection to the rate limiter backend if needed."""
        pass


rate_limiter_service = RateLimiterService()
