from typing import List

from nala.athomic.ai.governance.guards.base import BaseGuard
from nala.athomic.ai.governance.guards.keyword_blocklist import (
    KeywordBlocklistValidator,
)
from nala.athomic.ai.governance.guards.output_sanitizer import OutputPIISanitizer
from nala.athomic.ai.governance.guards.pii_sanitizer import RegexPIISanitizer
from nala.athomic.ai.governance.guards.protocol import (
    AIGuardOutputProtocol,
)
from nala.athomic.ai.governance.guards.rate_limiter import RateLimitGuard
from nala.athomic.ai.governance.pipeline import GuardPipeline
from nala.athomic.config.schemas.ai.governance import GovernanceSettings


class GuardFactory:
    """
    Factory responsible for composing and instantiating all active input and output
    Guardrail components based on injected application settings.
    """

    @classmethod
    def create(cls, settings: GovernanceSettings) -> GuardPipeline:
        """
        Creates the complete governance pipeline (input and output guards).

        Args:
            settings: The specific configuration for the AI Governance module.

        Returns:
            GuardPipeline instance ready for execution.
        """
        if not settings.enabled:
            return GuardPipeline(settings=settings.pipeline)

        input_guards: List[BaseGuard] = []
        output_guards: List[AIGuardOutputProtocol] = []

        # 1. Rate Limiting
        if settings.rate_limiter.enabled:
            input_guards.append(RateLimitGuard(policy_name="ai_default"))

        # 2. Keyword Blocking
        if settings.keyword_blocklist.enabled:
            input_guards.append(
                KeywordBlocklistValidator(
                    enabled=settings.keyword_blocklist.enabled,
                    blocklist=settings.keyword_blocklist.blocklist,
                )
            )

        # 3. PII Sanitization (Input)
        if settings.pii_sanitizer.enabled:
            input_guards.append(RegexPIISanitizer(settings=settings.pii_sanitizer))

        # 1. PII Sanitization (Output)
        if settings.pii_sanitizer.enabled:
            output_guards.append(OutputPIISanitizer(settings=settings.pii_sanitizer))

        active_input_guards = [g for g in input_guards if g.is_enabled()]

        active_output_guards = [
            g
            for g in output_guards
            if hasattr(g, "check_and_process") and g.is_enabled()
        ]

        return GuardPipeline(
            input_guards=active_input_guards,
            output_guards=active_output_guards,
            settings=settings.pipeline,
        )
