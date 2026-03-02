import pytest

from nala.athomic.observability.log.filters.sensitive_data_filter import (
    SensitiveDataFilter,
)
from nala.athomic.observability.log.maskers.base_masker import BaseMasker
from nala.athomic.observability.log.registry import MASKER_REGISTRY
from nala.athomic.observability.log.utils.log_mask_score import order_masker_instances


@pytest.fixture
def sensitive_filter() -> SensitiveDataFilter:
    """
    Instantiate the sensitive data filter with all registered maskers.
    """
    patterns = order_masker_instances(
        [m if isinstance(m, BaseMasker) else m() for m in MASKER_REGISTRY]
    )
    return SensitiveDataFilter(patterns=patterns)


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("Nothing sensitive here", "Nothing sensitive here"),
        ("My email is test@example.com", "***@***.***"),
        ("Credit card: 1234-5678-1234-5678", "****-****-****-5678"),
        ("User CPF: 123.456.789-01", "***.***.***-01"),
        (
            '"password": "SuperSecret123"',  # pragma: allowlist secret
            '"password": "REDACTED_PASSWORD"',  # pragma: allowlist secret
        ),
        (
            "api_key=abcd1234 test",  # pragma: allowlist secret
            "api_key=REDACTED_API_KEY test",  # pragma: allowlist secret
        ),
        (
            "Authorization: Bearer abcdef1234xyz",  # pragma: allowlist secret
            "Authorization: Bearer REDACTED_TOKEN",  # pragma: allowlist secret
        ),
        ("My phone is (11) 98765-4321", "(11) *****-**21"),
    ],
)
def test_sensitive_data_filter(
    sensitive_filter: SensitiveDataFilter, input_text: str, expected: str
):
    """
    Validate that masking patterns are working correctly.
    """
    result = sensitive_filter(input_text)
    assert expected in result
