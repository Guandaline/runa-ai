# src/nala/athomic/observability/log/maskers/phone_masker.py
import re
from typing import Match

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class PhoneMasker(BaseMasker):
    """
    A specific masker implementation for phone numbers (including cellphones).

    This masker uses named capture groups to redact the central digits of the
    number while preserving the area code (DDD) and the last two digits
    for smart auditing purposes.
    """

    def pattern(self) -> re.Pattern:
        """
        Returns the regex pattern for a phone number. It captures three
        named groups: 'ddd', 'middle' (4 or 5 digits), and 'end' (4 digits).
        """
        # Pattern: (Area Code/DDD) (Middle 4-5 digits) - (Last 4 digits)
        # It handles optional parentheses and spaces.
        return re.compile(r"\(?(?P<ddd>\d{2})\)?\s?(?P<middle>\d{4,5})-?(?P<end>\d{4})")

    def mask(self, match: Match) -> str:
        """
        Masks the phone number by redacting the middle digits and the first
        two digits of the end group, while preserving the DDD and the last
        two verification digits.
        """
        try:
            # Extract named groups
            ddd = match.group("ddd")
            middle = match.group("middle")
            end = match.group("end")

            # Redact the middle part entirely
            masked_middle = "*" * len(middle)

            # Smart masking: redact the first two digits of the end part, preserve the last two
            masked_end = "*" * (len(end) - 2) + end[-2:]

            # Reconstruct the string in a standard format
            return f"({ddd}) {masked_middle}-{masked_end}"
        except Exception as e:
            # Catch any unexpected failure during masking
            logger.error(f"ERROR in mask_cellphone_named_groups: {e}")
            return "MASK_PHONE_ERROR"
