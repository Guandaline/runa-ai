# src/nala/athomic/observability/log/maskers/base_masker.py
import re
from abc import ABC, abstractmethod
from typing import Match


class BaseMasker(ABC):
    """
    Abstract Base Class (ABC) for all sensitive data maskers within the Athomic framework.

    This class enforces the contract required by the SensitiveDataFilter,
    ensuring that every masker provides both a unique regex pattern and a
    specific masking implementation.
    """

    @abstractmethod
    def pattern(self) -> re.Pattern:
        """
        Returns the compiled regex pattern object that this masker is
        responsible for detecting.

        Returns:
            re.Pattern: The compiled regular expression.
        """
        pass

    @abstractmethod
    def mask(self, match: Match) -> str:
        """
        Receives the regex match object for the sensitive data and returns
        the masked (redacted) version of the data.

        This method should contain the core logic for intelligent masking.

        Args:
            match: The regex match object containing the captured sensitive data.

        Returns:
            str: The masked replacement string.
        """
        pass
