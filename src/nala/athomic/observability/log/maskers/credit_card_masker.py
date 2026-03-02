# src/nala/athomic/observability/log/maskers/credit_card_masker.py
import re
from typing import Match

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class CreditCardMasker(BaseMasker):
    """
    A specific masker implementation for credit card numbers.

    This masker complies with PCI DSS guidance by redacting all digits
    except the last four, which are necessary for auditing purposes.
    The pattern accommodates both hyphenated and non-hyphenated formats.
    """

    def pattern(self) -> re.Pattern:
        """
        Returns the regex pattern for a 16-digit credit card number,
        capturing the last four digits in a separate group.
        """
        # Captures four groups of four digits, with optional hyphens between them
        return re.compile(r"(\d{4})-?(\d{4})-?(\d{4})-?(\d{4})")

    def mask(self, match: Match) -> str:
        """
        Masks the credit card number, preserving only the last four digits
        and replacing the rest with asterisks and hyphens.

        Args:
            match: The regex match object for the credit card number.

        Returns:
            str: The PCI-compliant masked credit card string.
        """
        try:
            logger.debug("Executing CreditCardMasker")
            # Group 4 contains the last four digits (xxxx)
            last_four = match.group(4)
            if last_four:
                # Returns the redacted string preserving the last four digits
                return f"****-****-****-{last_four}"
            # Fallback if group 4 somehow matched empty string
            return "****-****-****-****"
        except IndexError:
            # Log a warning if the regex match structure was unexpected
            logger.warning(f"mask_credit_card IndexError for match: {match.group(0)}")
            return "****-****-****-XXXX"
        except Exception as e:
            # Log a general error if the masking process itself fails
            logger.error(f"ERROR in mask_credit_card: {e}")
            return "MASK_CARD_ERROR"
