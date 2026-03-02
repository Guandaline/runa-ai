import re
from typing import Any, Optional

from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.governance import PIISanitizerSettings

from .base import BaseOutputGuard


class OutputPIISanitizer(BaseOutputGuard):
    """
    Sanitizes the LLM's generated response by masking PII based on dynamic configuration.
    """

    def __init__(self, settings: Optional[PIISanitizerSettings] = None) -> None:
        if settings is None:
            settings = get_settings().ai.governance.pii_sanitizer

        super().__init__(policy_name="output_pii_sanitizer", enabled=settings.enabled)
        self.settings = settings

    async def _process(self, response: LLMResponse, **kwargs: Any) -> LLMResponse:
        """
        Concrete implementation of the processing logic.
        Only called if the guard is enabled.
        """
        if not response.content:
            return response

        sanitized_content = response.content
        modified = False

        for _, pii_pattern in self.settings.patterns.items():
            try:
                pattern = pii_pattern.regex
                replacement = pii_pattern.replacement

                new_sanitized_content = re.sub(pattern, replacement, sanitized_content)

                if new_sanitized_content != sanitized_content:
                    modified = True
                    sanitized_content = new_sanitized_content

            except re.error as e:
                self.logger.error(f"Invalid regex pattern: {e}")

        if modified:
            self.logger.warning("PII detected and masked in LLM output.")
            return response.model_copy(update={"content": sanitized_content})

        return response
