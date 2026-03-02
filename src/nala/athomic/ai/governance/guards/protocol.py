from typing import Any, Protocol, runtime_checkable

from nala.athomic.ai.schemas.llms import LLMResponse


@runtime_checkable
class AIGuardProtocol(Protocol):
    """
    Base interface shared by all AI Governance Guards.
    Ensures every guard allows inspection of its name and status.
    """

    @property
    def policy_name(self) -> str:
        """The unique name of the security policy implemented by this guard."""
        ...

    def is_enabled(self) -> bool:
        """Returns True if the guard is active and should be executed."""
        ...


@runtime_checkable
class AIGuardInputProtocol(AIGuardProtocol, Protocol):
    """
    Interface for Input Guards (Pre-execution).
    These guards validate the user prompt and raise exceptions on violation.
    """

    async def check(self, prompt: str, **kwargs: Any) -> None:
        """
        Validates the input prompt.

        Args:
            prompt: The raw user input or prompt string.
            **kwargs: Additional context (user_id, tenant_id, trace_id, etc.).

        Raises:
            SecurityPolicyViolationError: If content violates safety policies.
            QuotaExceededError: If rate limits are hit.
        """
        ...


@runtime_checkable
class AIGuardOutputProtocol(AIGuardProtocol, Protocol):
    """
    Interface for Output Guards (Post-execution).
    These guards inspect and potentially modify (sanitize) the LLM response.
    """

    async def check_and_process(
        self, response: LLMResponse, **kwargs: Any
    ) -> LLMResponse:
        """
        Validates and processes the LLM response.

        Args:
            response: The original response object from the LLM.
            **kwargs: Additional context.

        Returns:
            LLMResponse: The potentially modified/sanitized response.
        """
        ...
