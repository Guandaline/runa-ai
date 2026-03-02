# src/nala/athomic/observability/log/maskers/phone_masker.py
import re
from typing import Match, Optional

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class PhoneMasker(BaseMasker):
    def pattern(self) -> re.Pattern:
        """
        Regex to match phone numbers with or without parentheses around the area code.
        Cases:
        - (XX) 9XXXX-XXXX  (9 digits)
        - (XX) XXXX-XXXX   (8 digits)
        - XX 9XXXX-XXXX    (9 digits, no parentheses)
        - XX XXXX-XXXX     (8 digits, no parentheses)
        - XX9XXXXXXXX      (9 digits, no formatting)
        - XXXXXXXXXX       (8 digits, no formatting)

        Groups:
        - ddd: The two digits of the area code (captured regardless of parentheses)
        - middle: 4 or 5 middle digits
        - end: Last 4 digits
        """
        return re.compile(
            r"\b"
            r"\(?"
            r"(?P<ddd>\d{2})"
            r"\)?"
            r"\s?"
            r"(?P<middle>\d{4,5})"
            r"-?"
            r"(?P<end>\d{4})"
            r"\b"
        )

    def mask(self, match: Match) -> str:
        """Masks a phone number match by replacing middle digits with asterisks."""
        try:
            ddd: Optional[str] = match.group("ddd")
            middle: Optional[str] = match.group("middle")
            end: Optional[str] = match.group("end")

            if not ddd or not middle or not end:
                logger.warning(
                    f"PhoneMasker: Match object missing expected groups: {match.group(0)}"
                )
                return "MASK_PHONE_ERROR"

            masked_middle = "*" * len(middle)
            masked_end = "*" * (len(end) - 2) + end[-2:]

            return f"({ddd}) {masked_middle}-{masked_end}"

        except IndexError:
            logger.warning(
                f"PhoneMasker: IndexError accessing groups for match: {match.group(0)}"
            )
            return "MASK_PHONE_ERROR_INDEX"
        except Exception as e:
            logger.error(f"ERROR in PhoneMasker mask method: {e}")
            return "MASK_PHONE_ERROR"
