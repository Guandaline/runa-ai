# src/nala/athomic/observability/log/maskers/cpf_masker.py
import re
from typing import Match

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class CPFMasker(BaseMasker):
    """
    A specific masker implementation for Brazilian CPF numbers (Cadastro de Pessoas Físicas).

    This masker implements 'smart masking' by preserving the last two
    verification digits while redacting the rest of the PII.
    """

    def pattern(self) -> re.Pattern:
        """
        Returns the regex pattern for a standard, formatted CPF (XXX.XXX.XXX-XX).
        The last two digits are captured in a separate group.
        """
        return re.compile(r"(\d{3})\.(\d{3})\.(\d{3})-(\d{2})")

    def mask(self, match: Match) -> str:
        """
        Masks the CPF number by replacing all but the last two verification digits
        with asterisks.

        Args:
            match: The regex match object for the CPF.

        Returns:
            str: The smart-masked CPF string.
        """
        try:
            # Group 4 contains the last two verification digits (XX)
            last_two = match.group(4)
            if last_two:
                # Returns the redacted string preserving the verification digits
                return f"***.***.***-{last_two}"
            # Fallback if group 4 somehow matched empty string
            return "***.***.***-XX"
        except IndexError:
            # Log a warning if the regex match structure was unexpected
            logger.warning(f"mask_cpf IndexError for match: {match.group(0)}")
            return "***.***.***-XX"
        except Exception as e:
            # Log a general error if the masking process itself fails
            logger.error(f"ERROR in mask_cpf: {e}")
            return "MASK_CPF_ERROR"
