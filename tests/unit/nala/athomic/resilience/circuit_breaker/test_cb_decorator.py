# tests/unit/nala/athomic/resilience/circuit_breaker/test_cb_decorator.py
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.resilience.circuit_breaker import circuit_breaker

FACTORY_PATH = (
    "nala.athomic.resilience.circuit_breaker.decorator.CircuitBreakerFactory.create"
)


@patch(FACTORY_PATH)
@pytest.mark.asyncio
async def test_decorator_calls_service_execute(mock_factory_create):
    # Arrange: Mock the service that the factory will return
    mock_service = AsyncMock()
    mock_service.execute.return_value = "decorated function result"
    mock_factory_create.return_value = mock_service

    @circuit_breaker(name="my_test_circuit")
    async def my_function(arg1, kwarg1=None):
        return "original function result"

    # Act
    result = await my_function("A", kwarg1="B")

    # Assert
    assert result == "decorated function result"
    mock_factory_create.assert_called_once()
    mock_service.execute.assert_called_once()

    # Check that the service was called correctly by the decorator
    call_args, call_kwargs = mock_service.execute.call_args
    assert call_args[0] == "my_test_circuit"
    assert call_args[1] is my_function.__wrapped__
    assert call_args[2] == "A"
    assert call_kwargs == {"kwarg1": "B"}


@patch(FACTORY_PATH)
@pytest.mark.asyncio
async def test_decorator_infers_default_name(mock_factory_create):
    mock_service = AsyncMock()
    mock_factory_create.return_value = mock_service

    @circuit_breaker()
    async def my_awesome_function():
        """This is a sync function."""
        pass

    await my_awesome_function()

    mock_service.execute.assert_called_once()
    expected_name = "test_decorator_infers_default_name.<locals>.my_awesome_function"
    assert mock_service.execute.call_args[0][0] == expected_name


def test_decorator_raises_on_sync_function():
    with pytest.raises(TypeError, match="only supports async functions"):

        @circuit_breaker()
        def my_sync_function():
            """This is a sync function."""
            pass
