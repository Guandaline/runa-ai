import re
from typing import Any, Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.governance.governance_settings import (
    PIISanitizerSettings,
)

from .base import BaseInputGuard


class RegexPIISanitizer(BaseInputGuard):
    """
    Input Guard that detects Sensitive Data (PII) in the user prompt using Regex.
    Currently configured to LOG detections (Observability).
    """

    def __init__(self, settings: Optional[PIISanitizerSettings] = None) -> None:
        if settings is None:
            # Fallback seguro para as configurações globais
            settings = get_settings().ai.governance.pii_sanitizer

        super().__init__(policy_name="input_pii_detector", enabled=settings.enabled)
        self.settings = settings

    async def _validate(self, prompt: str, **kwargs: Any) -> None:
        """
        Scans the prompt for configured PII patterns and logs warnings if found.
        Does not block execution by default, but provides audit trails.
        """
        if not prompt:
            return

        for pii_type, pii_pattern in self.settings.patterns.items():
            try:
                if re.search(pii_pattern.regex, prompt):
                    # Structured logging for security audit
                    self.logger.info(
                        f"PII of type '{pii_type}' detected in input prompt. "
                        f"Trace ID: {kwargs.get('trace_id', 'unknown')}"
                    )
            except re.error as e:
                self.logger.error(
                    f"Invalid regex pattern for PII type '{pii_type}': {e}"
                )
