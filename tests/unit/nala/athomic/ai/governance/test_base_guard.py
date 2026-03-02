from typing import Any

import pytest

from nala.athomic.ai.governance.guards.base import BaseInputGuard


class ConcreteInputGuard(BaseInputGuard):
    """
    A concrete implementation of BaseInputGuard for testing purposes.
    Used to verify the Template Method behavior in the abstract base class.
    """

    def __init__(self, enabled: bool):
        super().__init__(policy_name="test_policy", enabled=enabled)
        self.validate_called = False
        self.captured_kwargs = {}

    async def _validate(self, prompt: str, **kwargs: Any) -> None:
        """
        Mock implementation of the protected abstract method.
        """
        self.validate_called = True
        self.captured_kwargs = kwargs


@pytest.mark.asyncio
async def test_base_guard_skips_execution_when_disabled():
    """
    Verifies that the guard logic is bypassed entirely if the guard is disabled.
    """
    # Arrange
    guard = ConcreteInputGuard(enabled=False)
    prompt = "Test Prompt"

    # Act
    await guard.check(prompt)

    # Assert
    assert (
        guard.validate_called is False
    ), "Guard should not execute policy when disabled"


@pytest.mark.asyncio
async def test_base_guard_executes_policy_when_enabled():
    """
    Verifies that the guard delegates to _validate when enabled.
    """
    # Arrange
    guard = ConcreteInputGuard(enabled=True)
    prompt = "Test Prompt"
    metadata = {"user_id": "123", "trace_id": "abc"}

    # Act
    await guard.check(prompt, **metadata)

    # Assert
    assert guard.validate_called is True, "Guard should execute policy when enabled"
    assert (
        guard.captured_kwargs == metadata
    ), "Context kwargs should be passed to the policy implementation"
