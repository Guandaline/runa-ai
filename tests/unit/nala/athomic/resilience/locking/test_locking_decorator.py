# tests/unit/nala/athomic/resilience/locking/test_locking_decorator.py
import asyncio
from typing import Generator
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest

from nala.athomic.resilience.locking.decorator import (
    _resolve_key,
    distributed_lock,
)
from nala.athomic.resilience.locking.exceptions import LockAcquisitionError
from nala.athomic.resilience.locking.protocol import LockingProtocol

LOCKING_FACTORY_PATH = "nala.athomic.resilience.locking.decorator.LockingFactory"


def sample_function_for_key_test(order_id: str, *, tenant_id: str = "default"):
    """Example function to test key resolution."""
    pass


def test_resolve_key_success():
    """Checks if the key is correctly formatted with args and kwargs."""
    # Arrange
    key_template = "order:{order_id}:tenant:{tenant_id}"
    args = ("order-123",)
    kwargs = {"tenant_id": "tenant-abc"}

    # Act
    resolved_key = _resolve_key(
        key_template, sample_function_for_key_test, args, kwargs
    )

    # Assert
    assert resolved_key == "order:order-123:tenant:tenant-abc"


def test_resolve_key_uses_default_value():
    """Checks if the key is formatted using the default value of a kwarg."""
    key_template = "order:{order_id}:tenant:{tenant_id}"
    args = ("order-123",)
    kwargs = {}

    resolved_key = _resolve_key(
        key_template, sample_function_for_key_test, args, kwargs
    )

    assert resolved_key == "order:order-123:tenant:default"


def test_resolve_key_missing_argument_raises_error():
    """Checks if a ValueError is raised if an argument in the template does not exist in the function."""
    key_template = "order:{order_id}:user:{user_id}"
    args = ("order-123",)
    kwargs = {}

    with pytest.raises(ValueError, match="Missing argument"):
        _resolve_key(key_template, sample_function_for_key_test, args, kwargs)


# --- Tests for the @distributed_lock decorator ---


@pytest.fixture
def mock_locking_provider() -> Generator[MagicMock, None, None]:
    """Fixture that mocks LockingFactory to return a mocked lock provider."""
    mock_provider = MagicMock(spec=LockingProtocol)

    mock_context_manager = AsyncMock()
    mock_provider.acquire.return_value = mock_context_manager

    with mock.patch(LOCKING_FACTORY_PATH) as mock_factory:
        mock_factory.create.return_value = mock_provider
        yield mock_provider


@pytest.mark.asyncio
async def test_lock_acquired_successfully(mock_locking_provider: MagicMock):
    """
    Tests the happy path: the lock is acquired and the original function is executed.
    """

    # Arrange
    @distributed_lock(key="process-item:{item_id}")
    async def process_item(item_id: int):
        return f"Processed {item_id}"

    # Act
    result = await process_item(item_id=123)

    # Assert
    assert result == "Processed 123"
    mock_locking_provider.acquire.assert_called_once_with(
        "process-item:123", timeout=30
    )
    mock_locking_provider.acquire.return_value.__aenter__.assert_awaited_once()


@pytest.mark.asyncio
async def test_lock_acquisition_times_out(mock_locking_provider: MagicMock):
    """
    Tests the failure path: the lock is not acquired and LockAcquisitionError is raised.
    """
    # Arrange
    # Set up the mock to raise TimeoutError when trying to acquire the lock
    mock_locking_provider.acquire.return_value.__aenter__.side_effect = (
        asyncio.TimeoutError
    )

    @distributed_lock(key="process-item:{item_id}", timeout=5)
    async def process_item(item_id: int):
        pytest.fail("The original function should not have been executed.")

    # Act & Assert
    with pytest.raises(LockAcquisitionError) as exc_info:
        await process_item(item_id=456)

    assert exc_info.value.key == "process-item:456"
    assert exc_info.value.timeout == 5
    mock_locking_provider.acquire.assert_called_once_with("process-item:456", timeout=5)


def test_decorator_raises_on_sync_function():
    """
    Checks if the decorator raises a TypeError when applied to a sync function.
    """
    with pytest.raises(TypeError, match="only supports async functions"):

        @distributed_lock(key="some-key")
        def my_sync_function():
            # Just a placeholder function
            pass
