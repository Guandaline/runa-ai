# src/nala/athomic/observability/log/maskers/email_masker.py
import re
from typing import Match

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class EmailMasker(BaseMasker):
    """
    A specific masker implementation designed to redact email addresses
    by replacing the local part, the '@' symbol, and the domain with asterisks.

    This ensures that PII is removed from logs while retaining a generic
    understanding that an email was present.
    """

    def pattern(self) -> re.Pattern:
        """
        Returns the regex pattern to detect a standard email address format.
        It allows for various characters in the local part and domain.
        """
        # Pattern: [\w\.+-]+ (local part, allowing letters, digits, dots, plus/minus)
        # followed by @, domain, and TLD (Top-Level Domain).
        return re.compile(r"[\w\.+-]+@[\w\.-]+\.[a-zA-Z]{2,}")

    def mask(self, match: Match) -> str:
        """
        Returns a generic masked string, ensuring that no part of the original
        email address is exposed.
        """
        return "***@***.***"
