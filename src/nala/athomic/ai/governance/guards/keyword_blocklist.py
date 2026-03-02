from typing import Any, List, Optional

from nala.athomic.config import get_settings

from ..exceptions import SecurityPolicyViolationError
from .base import BaseInputGuard


class KeywordBlocklistValidator(BaseInputGuard):
    """
    Input Guard that checks for forbidden keywords or topics in the prompt.
    Blocks the request if any listed term is found.
    """

    def __init__(
        self,
        enabled: bool = True,
        blocklist: Optional[List[str]] = None,
    ) -> None:
        """
        Args:
            enabled: Whether the guard is active.
            blocklist: List of forbidden strings. Defaults to settings if None.
        """
        super().__init__(policy_name="keyword_blocklist", enabled=enabled)

        if blocklist is None:
            blocklist = get_settings().ai.governance.keyword_blocklist.blocklist

        self.blocklist = [word.lower() for word in blocklist]

    async def _validate(self, prompt: str, **kwargs: Any) -> None:
        """
        Validates that the prompt does not contain any forbidden keywords.

        Raises:
            SecurityPolicyViolationError: If a keyword is found.
        """
        if not prompt:
            return

        prompt_lower = prompt.lower()

        for keyword in self.blocklist:
            if keyword in prompt_lower:
                self.logger.warning(
                    f"Blocked request containing forbidden keyword: '{keyword}'"
                )
                raise SecurityPolicyViolationError(
                    f"Request contains prohibited content (keyword: '{keyword}')."
                )
