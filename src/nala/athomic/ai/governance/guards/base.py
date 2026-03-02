from abc import ABC, abstractmethod
from typing import Any

from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.observability import get_logger

from .protocol import (
    AIGuardInputProtocol,
    AIGuardOutputProtocol,
)


class BaseGuard(ABC):
    """
    Root base class for all AI Governance Guards.
    Holds shared state like enabled status, policy naming, and logging.
    """

    def __init__(self, policy_name: str, enabled: bool = True) -> None:
        self._policy_name = policy_name
        self._enabled = enabled
        self.logger = get_logger(f"ai.governance.guard.{policy_name}")

    @property
    def policy_name(self) -> str:
        """Implementation of the protocol's policy_name property."""
        return self._policy_name

    def is_enabled(self) -> bool:
        return self._enabled


class BaseInputGuard(BaseGuard, AIGuardInputProtocol):
    """
    Base class specifically for Input Guards (Prompt Validation).
    Implements the template method for 'check'.
    """

    async def check(self, prompt: str, **kwargs: Any) -> None:
        """
        Template method: Checks if enabled, logs, then delegates to specific logic.
        Raises SecurityPolicyViolationError if validation fails.
        """
        if not self.is_enabled():
            return

        self.logger.debug(f"Executing Input Check: '{self.policy_name}'")
        await self._validate(prompt, **kwargs)

    @abstractmethod
    async def _validate(self, prompt: str, **kwargs: Any) -> None:
        """Concrete validation logic to be implemented by subclasses."""
        pass


class BaseOutputGuard(BaseGuard, AIGuardOutputProtocol):
    """
    Base class specifically for Output Guards (Response Sanitization).
    Implements the template method for 'check_and_process'.
    """

    async def check_and_process(
        self, response: LLMResponse, **kwargs: Any
    ) -> LLMResponse:
        """
        Template method: Checks if enabled, logs, then delegates to processing logic.
        Returns the (potentially modified) response.
        """
        if not self.is_enabled():
            return response

        self.logger.debug(f"Executing Output Processing: '{self.policy_name}'")
        return await self._process(response, **kwargs)

    @abstractmethod
    async def _process(self, response: LLMResponse, **kwargs: Any) -> LLMResponse:
        """Concrete processing logic to be implemented by subclasses."""
        pass
