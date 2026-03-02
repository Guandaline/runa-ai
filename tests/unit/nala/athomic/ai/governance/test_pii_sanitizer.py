from typing import Any, Dict
from unittest.mock import MagicMock, call

import pytest

from nala.athomic.ai.governance.guards.pii_sanitizer import RegexPIISanitizer
from nala.athomic.config.schemas.ai.governance import PIIPattern, PIISanitizerSettings


@pytest.fixture
def pii_settings() -> PIISanitizerSettings:
    """Creates a controlled settings object with known regex patterns."""
    return PIISanitizerSettings(
        enabled=True,
        patterns={
            "EMAIL": PIIPattern(
                regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                replacement="<EMAIL_REDACTED>",
            ),
            "PHONE": PIIPattern(
                regex=r"\d{3}-\d{3}-\d{4}",
                replacement="<PHONE_REDACTED>",
            ),
        },
    )


@pytest.mark.asyncio
async def test_pii_sanitizer_detects_email_in_prompt(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies that the guard logic detects PII and logs it correctly.
    """
    # Arrange
    guard = RegexPIISanitizer(settings=pii_settings)
    guard.logger = MagicMock()

    prompt = "Please contact me at john.doe@example.com for details."
    context: Dict[str, Any] = {"trace_id": "test-trace-123"}

    # Act
    await guard.check(prompt, **context)

    # Assert
    expected_msg = (
        "PII of type 'EMAIL' detected in input prompt. Trace ID: test-trace-123"
    )
    guard.logger.info.assert_called_with(expected_msg)


@pytest.mark.asyncio
async def test_pii_sanitizer_detects_multiple_patterns(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies that multiple different PII types are detected in a single pass.
    """
    # Arrange
    guard = RegexPIISanitizer(settings=pii_settings)
    guard.logger = MagicMock()

    prompt = "Email: jane@test.org, Phone: 555-019-1234"
    context: Dict[str, Any] = {"trace_id": "unknown"}

    # Act
    await guard.check(prompt, **context)

    # Assert
    expected_calls = [
        call("PII of type 'EMAIL' detected in input prompt. Trace ID: unknown"),
        call("PII of type 'PHONE' detected in input prompt. Trace ID: unknown"),
    ]

    guard.logger.info.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.asyncio
async def test_pii_sanitizer_does_not_trigger_on_clean_prompt(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies that prompts without PII do not trigger detection logs.
    """
    # Arrange
    guard = RegexPIISanitizer(settings=pii_settings)
    guard.logger = MagicMock()

    prompt = "This is a safe prompt with no sensitive data."
    context: Dict[str, Any] = {}

    # Act
    await guard.check(prompt, **context)

    # Assert
    guard.logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_pii_sanitizer_handles_empty_prompt(
    pii_settings: PIISanitizerSettings,
) -> None:
    """
    Verifies behavior when the prompt is None or empty.
    """
    # Arrange
    guard = RegexPIISanitizer(settings=pii_settings)
    guard.logger = MagicMock()
    context: Dict[str, Any] = {}

    # Act
    await guard.check(None, **context)  # type: ignore

    # Assert
    guard.logger.info.assert_not_called()


@pytest.mark.asyncio
async def test_pii_sanitizer_handles_invalid_regex() -> None:
    """
    Verifies that an invalid regex pattern handles errors gracefully.
    """
    # Arrange
    bad_settings = PIISanitizerSettings(
        enabled=True,
        patterns={
            "BAD_REGEX": PIIPattern(regex=r"[", replacement="<ERR>")  # Invalid syntax
        },
    )
    guard = RegexPIISanitizer(settings=bad_settings)
    guard.logger = MagicMock()

    prompt = "Some text."
    context: Dict[str, Any] = {}

    # Act
    await guard.check(prompt, **context)

    # Assert
    args, _ = guard.logger.error.call_args
    assert "Invalid regex pattern for PII type 'BAD_REGEX'" in args[0]
