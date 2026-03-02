import pytest

from nala.athomic.ai.governance.guards.output_sanitizer import OutputPIISanitizer
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config.schemas.ai.governance import PIIPattern, PIISanitizerSettings


@pytest.fixture
def pii_settings() -> PIISanitizerSettings:
    """Creates settings with a standard email masking pattern."""
    return PIISanitizerSettings(
        enabled=True,
        patterns={
            "EMAIL": PIIPattern(
                regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                replacement="<REDACTED_EMAIL>",
            )
        },
    )


@pytest.mark.asyncio
async def test_output_sanitizer_masks_response_content(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies that sensitive data in the LLM response content is masked.
    """
    # Arrange
    guard = OutputPIISanitizer(settings=pii_settings)
    original_response = LLMResponse(
        content="The admin email is admin@corp.com.",
        model="gpt-4",
        finish_reason="stop",
    )

    # Act
    sanitized_response = await guard.check_and_process(original_response)

    # Assert
    expected_content = "The admin email is <REDACTED_EMAIL>."
    assert sanitized_response.content == expected_content
    # Metadata should remain unchanged
    assert sanitized_response.model == "gpt-4"
    assert sanitized_response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_output_sanitizer_returns_original_if_disabled() -> None:
    """
    Verifies that if the sanitizer settings are disabled, the response is returned untouched.
    """
    # Arrange
    disabled_settings = PIISanitizerSettings(enabled=False, patterns={})
    guard = OutputPIISanitizer(settings=disabled_settings)

    original_response = LLMResponse(
        content="Secret: admin@corp.com",
        model="gpt-4",
        finish_reason="stop",
    )

    # Act
    result = await guard.check_and_process(original_response)

    # Assert
    assert result.content == "Secret: admin@corp.com"
    assert result.model == "gpt-4"


@pytest.mark.asyncio
async def test_output_sanitizer_handles_empty_content(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies behavior when the response content is None or empty.
    """
    # Arrange
    guard = OutputPIISanitizer(settings=pii_settings)
    empty_response = LLMResponse(content="", model="gpt-4", finish_reason="stop")

    # Act
    result = await guard.check_and_process(empty_response)

    # Assert
    assert result.content == ""


@pytest.mark.asyncio
async def test_output_sanitizer_preserves_usage_metrics(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies that token usage and other extra fields are preserved after sanitization.
    """
    # Arrange
    guard = OutputPIISanitizer(settings=pii_settings)
    original_response = LLMResponse(
        content="Hello user@test.com",
        model="gpt-4",
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
    )

    # Act
    result = await guard.check_and_process(original_response)

    # Assert
    assert result.content == "Hello <REDACTED_EMAIL>"
    # Verify properties of the TokenUsage object instead of comparing to dict
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 5
