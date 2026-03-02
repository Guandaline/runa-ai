# src/nala/athomic/observability/log/filters/sensitive_data_filter.py
import re
from typing import Callable, List, Union

from loguru import logger

from nala.athomic.observability.log.maskers.base_masker import BaseMasker
from nala.athomic.observability.log.utils.log_mask_score import order_masker_instances


class SensitiveDataFilter:
    """
    A callable filter designed to sanitize log messages by redacting or
    masking sensitive data (PII, secrets, tokens) before they are written
    to any sink.

    This filter is the core enforcement mechanism for log compliance and security.
    """

    def __init__(
        self,
        patterns: List[
            tuple[Union[str, re.Pattern], Union[str, Callable[[re.Match], str]]]
        ],
        # The 'repl' argument is not used here but is kept for future expansion
        repl: str = "***REDACTED***",
    ) -> None:
        """
        Initializes the filter by compiling all registered and configured patterns.

        Args:
            patterns: A list of maskers/patterns, potentially unsorted.
            repl: Default replacement string (not currently used in internal logic).
        """
        # 1. Order maskers based on complexity score (e.g., specific regex before generic ones)
        ordered_patterns = order_masker_instances(patterns)

        self.compiled_patterns = []
        for item in ordered_patterns:
            pattern: Union[str, re.Pattern]
            repl_func_or_str: Union[str, Callable[[re.Match], str]]

            if isinstance(item, BaseMasker):
                # Handle BaseMasker instances (e.g., CPFMasker)
                pattern = item.pattern()
                repl_func_or_str = item.mask
            elif isinstance(item, tuple):
                # Handle direct tuple patterns (regex string/object + replacement string/callable)
                pattern, repl_func_or_str = item
            else:
                # Catch any unexpected type in the configuration list
                raise TypeError(f"Unsupported pattern type: {type(item)}")

            # Compile the pattern if it is a string, otherwise use the re.Pattern object
            compiled_pattern = (
                re.compile(pattern) if isinstance(pattern, str) else pattern
            )

            self.compiled_patterns.append(
                (
                    compiled_pattern,
                    repl_func_or_str,
                )
            )

    def _mask_data(self, text: str) -> str:
        """
        Applies all compiled patterns sequentially to the input text.
        """
        current_text = text

        for pattern, repl_func_or_str in self.compiled_patterns:
            try:
                # Check if the replacement is a callable (lambda or method)
                if callable(repl_func_or_str):
                    # Use re.sub with a lambda to pass the match object to the callable replacement function
                    # The lambda ensures that repl_func_or_str is captured correctly in the closure
                    current_text = pattern.sub(
                        lambda m, repl_func_or_str=repl_func_or_str: repl_func_or_str(
                            m
                        ),
                        current_text,
                    )
                else:
                    # Standard string replacement
                    current_text = pattern.sub(repl_func_or_str, current_text)
            except Exception as e:
                # Log error but continue to the next pattern (resilience)
                logger.opt(exception=True).error(
                    f"Error applying pattern {pattern.pattern}: {type(e).__name__} - {e}"
                )

        return current_text

    def __call__(self, message: str) -> str:
        """
        Makes the filter instance callable, which is the contract required by Loguru.
        """
        # Ensure the filter is robust against its own internal errors
        try:
            return self._mask_data(message)
        except Exception as e:
            logger.opt(exception=True).error(
                f"Critical error in SensitiveDataFilter __call__: {e}"
            )
            # If the filter itself fails critically, return the original message (unmasked)
            # to prevent the logging sink from failing entirely. This prioritizes availability over security.
            return message
