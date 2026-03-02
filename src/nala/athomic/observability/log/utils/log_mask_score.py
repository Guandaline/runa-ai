# src/nala/athomic/observability/log/utils/log_mask_score.py
import re
from typing import Callable, List, Tuple, Union

from nala.athomic.observability.log.maskers.base_masker import BaseMasker

# Alias for a tuple containing a regex pattern and its replacement mechanism
RegexType = Tuple[Union[str, re.Pattern], Union[str, Callable[[re.Match], str]]]


def score_regex_pattern(pattern: Union[str, re.Pattern]) -> int:
    """
    Generates a specificity score for a regex pattern to determine its execution order.
    More specific patterns receive a higher score and are executed first.
    This is critical to ensure that generic rules (e.g., 'any string') do not
    mask specific rules (e.g., 'CPF format').
    """
    if isinstance(pattern, re.Pattern):
        regex_str = pattern.pattern
    else:
        regex_str = pattern

    score = 0

    # 1. High Bonus: Prioritize unique identifiers or specific prefixes (High Precision)
    if any(
        token in regex_str
        for token in [
            "xoxb-",  # Slack tokens
            "xoxp-",
            "xapp-",
            "BEGIN",  # Private Keys
            "Bearer",  # Authorization headers
            "eyJ",  # JWT prefix
            "@",  # Emails
            "api_key",  # Query params/JSON keys
            "password",
        ]
    ):
        score += 15

    # 2. Length/Specificity Bonus: Reward longer minimum matches
    # Finds minimum length quantifiers like {12} or {4,5}
    quantifiers = re.findall(r"\{(\d{2,})\}", regex_str)
    if quantifiers:
        score += max(map(int, quantifiers)) // 2

    # 3. Penalty: Penalize generic boundaries or structures
    # Penalize starting with a word boundary (often too generic)
    if regex_str.startswith(r"\b"):
        score -= 5

    # Penalize overly generic capture groups (e.g., capturing everything)
    if re.search(r"\(\.\+|\(\[\^", regex_str):
        score -= 3

    # 4. Readability/Complexity Bonus: Reward structured complexity
    # Bonus for using named groups (often indicates a structural match)
    if re.search(r"\?P<\w+>", regex_str):
        score += 5

    # Simple metric for general structural complexity (parentheses, brackets, etc.)
    complexity = len(re.findall(r"[()\[\]{}|+?*]", regex_str))
    score += complexity // 2

    return score


def order_masker_instances(maskers: List[BaseMasker]) -> List[BaseMasker]:
    """
    Orders the list of BaseMasker instances based on the specificity score
    of their underlying regex patterns (descending order).

    The most specific patterns are placed at the beginning of the chain.

    Args:
        maskers: A list of concrete BaseMasker instances.

    Returns:
        List[BaseMasker]: A new list containing the maskers sorted by score.
    """
    # Uses a negative score for descending sort (highest score first)
    return sorted(maskers, key=lambda m: -score_regex_pattern(m.pattern()))
