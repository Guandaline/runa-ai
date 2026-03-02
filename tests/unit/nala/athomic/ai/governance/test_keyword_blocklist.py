from unittest.mock import MagicMock, patch

import pytest

from nala.athomic.ai.governance.exceptions import SecurityPolicyViolationError
from nala.athomic.ai.governance.guards.keyword_blocklist import (
    KeywordBlocklistValidator,
)


@pytest.mark.asyncio
async def test_keyword_validator_passes_safe_prompt() -> None:
    """
    Verifies that a prompt containing no blocked keywords passes validation.
    """
    # Arrange
    guard = KeywordBlocklistValidator(enabled=True, blocklist=["forbidden"])
    safe_prompt = "This is a completely safe prompt."

    # Act & Assert
    # Should not raise any exception
    await guard.check(safe_prompt)


@pytest.mark.asyncio
async def test_keyword_validator_raises_on_violation() -> None:
    """
    Verifies that the validator raises SecurityPolicyViolationError when a keyword is found.
    """
    # Arrange
    guard = KeywordBlocklistValidator(enabled=True, blocklist=["attack", "hack"])
    unsafe_prompt = "I want to perform a hack on the system."

    # Act & Assert
    with pytest.raises(SecurityPolicyViolationError) as exc_info:
        await guard.check(unsafe_prompt)

    assert "contains prohibited content" in str(exc_info.value)
    assert "hack" in str(exc_info.value)


@pytest.mark.asyncio
async def test_keyword_validator_is_case_insensitive() -> None:
    """
    Verifies that the matching logic ignores case differences.
    """
    # Arrange
    guard = KeywordBlocklistValidator(enabled=True, blocklist=["DROP TABLE"])
    # Input is lowercase, blocklist is uppercase
    unsafe_prompt = "please drop table users;"

    # Act & Assert
    with pytest.raises(SecurityPolicyViolationError) as exc_info:
        await guard.check(unsafe_prompt)

    assert "drop table" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_keyword_validator_uses_defaults_if_none_provided() -> None:
    """
    Verifies that the default blocklist is used if no list is provided during init.
    We mock get_settings to simulate the default configuration.
    """
    # Arrange
    mock_settings = MagicMock()
    # Simulate a default blocklist in settings
    mock_settings.ai.governance.keyword_blocklist.blocklist = ["sql injection"]

    with patch(
        "nala.athomic.ai.governance.guards.keyword_blocklist.get_settings",
        return_value=mock_settings,
    ):
        guard = KeywordBlocklistValidator(enabled=True, blocklist=None)

        # Act & Assert
        unsafe_prompt = "Attempting a sql injection attack."
        with pytest.raises(SecurityPolicyViolationError):
            await guard.check(unsafe_prompt)


@pytest.mark.asyncio
async def test_keyword_validator_ignores_empty_prompt() -> None:
    """
    Verifies that empty or None prompts do not trigger errors.
    """
    # Arrange
    guard = KeywordBlocklistValidator(enabled=True)

    # Act & Assert
    await guard.check(None)  # type: ignore
    await guard.check("")
