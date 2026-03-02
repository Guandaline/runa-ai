import re

from nala.athomic.observability.log.maskers.pattern_only import PatternOnlyMasker
from nala.athomic.observability.log.utils.log_mask_score import (
    order_masker_instances,
    score_regex_pattern,
)


def dummy_masker(match: re.Match) -> str:
    return "MASKED"


def test_score_regex_pattern_prioritizes_specific():
    pattern_generic = r".+"
    pattern_specific = r"xoxb-\d{12}-\d{12}-\d{12}-[a-z0-9]{32}"
    assert score_regex_pattern(pattern_specific) > score_regex_pattern(pattern_generic)


def test_order_sensitive_patterns_prioritizes_specific_patterns():
    p1 = PatternOnlyMasker(r".+", "GENERIC")
    p2 = PatternOnlyMasker(r"xoxb-\d{12}-\d{12}-\d{12}-[a-z0-9]{32}", "SLACK")

    ordered = order_masker_instances([p1, p2])
    assert isinstance(ordered[0], PatternOnlyMasker)
    assert ordered[0].pattern().pattern == p2.pattern().pattern


def test_order_sensitive_patterns_maintains_pairing():
    p1 = PatternOnlyMasker(r".+", "GENERIC")
    p2 = PatternOnlyMasker(r"xoxb-\d{12}-\d{12}-\d{12}-[a-z0-9]{32}", "SLACK")

    ordered = order_masker_instances([p1, p2])
    assert len(ordered) == 2
    assert isinstance(ordered[0], PatternOnlyMasker)
