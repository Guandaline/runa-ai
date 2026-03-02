# src/nala/athomic/observability/log/maskers/pattern_only.py
import re
from typing import Callable, Match, Union

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker


class PatternOnlyMasker(BaseMasker):
    """
    A generic masker implementation that allows any regex pattern and
    a corresponding replacement string or function to be defined at runtime.

    This class serves as the general-purpose tool for redacting secrets,
    tokens, or simple PII using explicit configuration.
    """

    def __init__(
        self,
        pattern: Union[str, re.Pattern],
        replacement: Union[str, Callable[[Match], str]],
    ) -> None:
        """
        Initializes the masker with the pattern and replacement mechanism.

        Args:
            pattern: The regex pattern (string or compiled re.Pattern).
            replacement: The replacement value. Can be a static string,
                         a string with backreferences (e.g., r'\\1'), or
                         a callable function that accepts a Match object.
        """
        # Compile the pattern if it's provided as a string
        self._pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.replacement = replacement

    def pattern(self) -> re.Pattern:
        """Returns the compiled regex pattern."""
        return self._pattern

    def mask(self, match: Match) -> str:
        """
        Applies the masking logic based on the replacement type:
        callable, backreference expansion, or static string.
        """
        try:
            # Case 1: Replacement is a callable (custom logic)
            if callable(self.replacement):
                return self.replacement(match)

            # Case 2: Replacement contains backreferences (e.g., r'\g<1>', r'\1')
            if "\\" in self.replacement:
                # Uses match.expand to resolve regex backreferences
                return match.expand(self.replacement)

            # Case 3: Simple static replacement string
            return self.replacement
        except Exception as e:
            logger.error(f"Error in PatternOnlyMasker: {e}")
            return "MASK_ERROR"
