import re

from nala.athomic.observability.log.maskers.credit_card_masker import CreditCardMasker

cc_masker = CreditCardMasker()
cc_pattern = cc_masker.pattern()


def test_credit_card_masker_pattern():
    """Verifies the CreditCardMasker regex pattern."""
    assert isinstance(cc_pattern, re.Pattern)
    assert cc_pattern.match("1234-5678-9012-3456") is not None
    assert cc_pattern.match("1234567890123456") is not None  # Without hyphens
    assert cc_pattern.match("1234-5678-9012-ABCD") is None


def test_credit_card_masker_mask_with_hyphens():
    """Tests masking with hyphens."""
    test_cc = "1234-5678-9012-3456"
    match = cc_pattern.search(test_cc)
    assert match is not None
    masked_result = cc_masker.mask(match)
    assert masked_result == "****-****-****-3456"


def test_credit_card_masker_mask_without_hyphens():
    """Tests masking without hyphens."""
    test_cc = "9876543210987654"
    match = cc_pattern.search(test_cc)
    assert match is not None
    masked_result = cc_masker.mask(match)
    # The mask always returns with hyphens by default in this masker
    assert masked_result == "****-****-****-7654"


def test_credit_card_masker_in_text():
    """Tests masking in text."""
    text = "CC: 1111-2222-3333-4444 is the number."
    match = cc_pattern.search(text)
    assert match is not None
    masked_result = cc_masker.mask(match)
    assert masked_result == "****-****-****-4444"

    masked_text = cc_pattern.sub(lambda m: cc_masker.mask(m), text)
    assert masked_text == "CC: ****-****-****-4444 is the number."
