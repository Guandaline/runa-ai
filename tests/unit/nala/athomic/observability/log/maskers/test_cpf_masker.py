import re

from nala.athomic.observability.log.maskers.cpf_masker import CPFMasker

# Instantiate the masker once for the tests
cpf_masker = CPFMasker()
cpf_pattern = cpf_masker.pattern()  # Get the compiled pattern


def test_cpf_masker_pattern():
    """Checks if the regex pattern of CPFMasker is correct."""
    assert isinstance(
        cpf_pattern, re.Pattern
    ), "pattern() should return a compiled regex pattern"
    # Check some examples that should and should not match
    assert cpf_pattern.match("123.456.789-00") is not None
    assert cpf_pattern.match("12345678900") is None  # Unformatted should not match
    assert cpf_pattern.match("abc.def.ghi-jk") is None


def test_cpf_masker_mask_valid():
    """Tests the mask function with a valid CPF."""
    test_cpf = "123.456.789-00"
    match = cpf_pattern.search(test_cpf)
    assert match is not None, "Regex should match the test CPF"

    masked_result = cpf_masker.mask(match)
    assert masked_result == "***.***.***-00"


def test_cpf_masker_mask_in_text():
    """Tests masking when the CPF is in the middle of a text."""
    text = "The user's CPF is 987.654.321-99 and must be protected."
    match = cpf_pattern.search(text)
    assert match is not None, "Regex should find the CPF in text"

    masked_result = cpf_masker.mask(match)
    assert masked_result == "***.***.***-99"

    # Test applying the substitution in the full text
    masked_text = cpf_pattern.sub(lambda m: cpf_masker.mask(m), text)
    assert masked_text == "The user's CPF is ***.***.***-99 and must be protected."
