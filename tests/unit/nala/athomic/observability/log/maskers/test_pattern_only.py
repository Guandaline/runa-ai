import re

from nala.athomic.observability.log.maskers.pattern_only import PatternOnlyMasker


def test_pattern_only_callable_replacement():
    pattern = r"card=(\d{4})-(\d{4})"

    def _mask_card_callable(match: re.Match) -> str:
        if match and match.group(2):
            return f"card=****-{match.group(2)}"
        return "card=****-ERR"

    replacement_func = _mask_card_callable
    masker = PatternOnlyMasker(pattern, replacement_func)
    pattern_compiled = masker.pattern()

    text = "Payment with card=1234-5678 failed."
    match = pattern_compiled.search(text)
    assert match is not None
    assert masker.mask(match) == "card=****-5678"

    masked_text = pattern_compiled.sub(replacement_func, text)
    assert masked_text == "Payment with card=****-5678 failed."
