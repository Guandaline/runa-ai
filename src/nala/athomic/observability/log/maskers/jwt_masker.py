# src/nala/athomic/observability/log/maskers/jwt_masker.py
import re
from typing import Match

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class JWTMasker(BaseMasker):
    """
    A specific masker implementation designed to detect and redact JWTs
    (JSON Web Tokens) from log messages.

    A JWT is typically identified by its three parts separated by dots
    and the "eyJ" prefix in the header.
    """

    def pattern(self) -> re.Pattern:
        """
        Returns the regex pattern for a standard JWT format:
        Base64UrlHeader.Base64UrlPayload.Base64UrlSignature.
        """
        # Pattern: Starts with 'eyJ' followed by three Base64Url-like segments separated by dots.
        # This is a highly specific and reliable pattern for identifying JWTs.
        return re.compile(r"eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+")

    def mask(self, match: Match) -> str:
        """
        Returns a generic, clear replacement string to indicate that a
        JWT was present and successfully redacted.
        """
        return "***REDACTED_JWT***"
