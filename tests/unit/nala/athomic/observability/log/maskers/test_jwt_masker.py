import re

from nala.athomic.observability.log.maskers.jwt_masker import JWTMasker

jwt_masker = JWTMasker()
jwt_pattern = jwt_masker.pattern()

# Example JWT (valid structure, irrelevant content)
SAMPLE_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"  # pragma: allowlist secret
INVALID_JWT_STRUCTURE = (
    "eyJhbGciOiJIUzI1NiJ9..SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)
NOT_JWT = "this.is.not.a.jwt"


def test_jwt_masker_pattern():
    """Verifies the JWTMasker regex pattern."""
    assert isinstance(jwt_pattern, re.Pattern)
    assert jwt_pattern.fullmatch(SAMPLE_JWT) is not None
    assert (
        jwt_pattern.fullmatch(INVALID_JWT_STRUCTURE) is None
    )  # Should have 3 non-empty parts
    assert jwt_pattern.fullmatch(NOT_JWT) is None


def test_jwt_masker_mask_valid():
    """Tests masking with valid JWT."""
    match = jwt_pattern.search(SAMPLE_JWT)
    assert match is not None
    masked_result = jwt_masker.mask(match)
    assert masked_result == "***REDACTED_JWT***"


def test_jwt_masker_in_text():
    """Tests masking in text."""
    text = f"Bearer {SAMPLE_JWT} was used to authenticate."
    match = jwt_pattern.search(text)
    assert match is not None
    masked_result = jwt_masker.mask(match)
    assert masked_result == "***REDACTED_JWT***"

    masked_text = jwt_pattern.sub(lambda m: jwt_masker.mask(m), text)
    assert masked_text == "Bearer ***REDACTED_JWT*** was used to authenticate."
