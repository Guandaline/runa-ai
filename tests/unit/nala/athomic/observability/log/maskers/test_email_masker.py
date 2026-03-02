import re

import pytest

from nala.athomic.observability.log.maskers.email_masker import EmailMasker

email_masker = EmailMasker()
email_pattern = email_masker.pattern()


def test_email_masker_pattern():
    """Verifies the EmailMasker regex pattern."""
    assert isinstance(email_pattern, re.Pattern)
    assert email_pattern.match("test@example.com") is not None
    assert email_pattern.match("test.user+alias@example.co.uk") is not None
    assert email_pattern.match("test@example") is None  # Invalid domain
    assert email_pattern.match("test@.com") is None
    assert email_pattern.match("test user@example.com") is None


@pytest.mark.parametrize(
    "email_input",
    [
        "test@example.com",
        "firstname.lastname@example.co.uk",
        "user+tag@domain.info",
        "_______@example.io",
    ],
)
def test_email_masker_mask_valid(email_input):
    """Tests masking with valid emails."""
    match = email_pattern.search(email_input)
    assert match is not None, f"Regex should match {email_input}"
    masked_result = email_masker.mask(match)
    assert masked_result == "***@***.***"


def test_email_masker_in_text():
    """Tests masking in text."""
    text = "Contact: john@provider.net or jane@another.org."
    # Uses finditer to get all occurrences
    matches = list(email_pattern.finditer(text))
    assert len(matches) == 2

    masked_text = email_pattern.sub(lambda m: email_masker.mask(m), text)
    assert masked_text == "Contact: ***@***.*** or ***@***.***."
