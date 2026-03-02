"""
AI Governance Guard implementation using the Athomic Resilience Rate Limiter.
Acts as an adapter between AI requests and the centralized RateLimiterService.
"""

from typing import Any, Optional

from nala.athomic.ai.governance.exceptions import QuotaExceededError
from nala.athomic.ai.governance.guards.base import BaseInputGuard
from nala.athomic.context import context_vars
from nala.athomic.context.generator import ContextKeyGenerator
from nala.athomic.resilience.rate_limiter.service import (
    RateLimiterService,
    rate_limiter_service,
)


class RateLimitGuard(BaseInputGuard):
    """
    Input Guard that enforces rate limits for AI requests.
    Reliably uses the global execution context for key generation.
    """

    def __init__(
        self,
        policy_name: str,
        service: Optional[RateLimiterService] = None,
        enabled: bool = True,
    ) -> None:
        super().__init__(policy_name=policy_name, enabled=enabled)
        self.service = service or rate_limiter_service
        self.key_generator = ContextKeyGenerator(namespace="ai_governance")

    async def _validate(self, prompt: str, **kwargs: Any) -> None:
        """
        Validates if the request is within the rate limits.
        """
        if not self.service.is_ready():
            self.logger.warning(
                f"RateLimiter service is not ready. Bypassing check for policy '{self.policy_name}'."
            )
            return

        rate_limit_key = self._get_identifier()

        is_allowed = await self.service.check(self.policy_name, rate_limit_key)

        if not is_allowed:
            self.logger.warning(
                f"Rate limit exceeded. Key: '{rate_limit_key}', Policy: '{self.policy_name}'"
            )
            raise QuotaExceededError(
                f"Rate limit exceeded for policy '{self.policy_name}'. Please try again later."
            )

    def _get_identifier(self) -> str:
        """
        Generates the context-aware key for the rate limiter.

        It relies entirely on ContextKeyGenerator for structure (prefix, tenant, user).
        If no user is present in the global context, it explicitly adds the Source IP
        to ensure anonymous users are rate-limited individually.
        """
        key_parts = [self.policy_name]

        if not context_vars.get_user_id():
            source_ip = context_vars.get_source_ip()
            if source_ip:
                key_parts.append(f"ip:{source_ip}")
            else:
                key_parts.append("anonymous")

        return self.key_generator.generate(*key_parts)
