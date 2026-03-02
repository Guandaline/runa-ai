# tests/athomic/resilience/rate_limiter/test_limits_provider.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nala.athomic.config.schemas.resilience.rate_limiter.providers.limits_provider_config import (
    LimitsProviderSettings,
)
from nala.athomic.config.schemas.resilience.rate_limiter.rate_limiter_config import (
    RateLimiterSettings,
)
from nala.athomic.resilience.rate_limiter.providers.limits_provider import (
    LimitsRateLimiter,
)

pytestmark = pytest.mark.asyncio


@patch(
    "nala.athomic.resilience.rate_limiter.providers.limits_provider.FixedWindowRateLimiter"
)
@patch("nala.athomic.resilience.rate_limiter.providers.limits_provider.MemoryStorage")
async def test_limits_provider_initialization_with_memory(
    mock_memory_storage: MagicMock, mock_strategy: MagicMock
):
    """
    Unit Test: Ensures the provider initializes the correct storage and strategy
    based on its configuration.
    """
    # Arrange
    provider_settings = LimitsProviderSettings(
        storage_backend="memory", strategy="fixed-window"
    )
    settings = RateLimiterSettings(backend="limits", provider=provider_settings)

    # Act
    provider = LimitsRateLimiter(settings=settings)

    # Assert
    # Check if MemoryStorage was instantiated
    mock_memory_storage.assert_called_once()
    # Check if the strategy was instantiated with the storage instance
    mock_strategy.assert_called_once_with(mock_memory_storage.return_value)
    assert provider.storage == mock_memory_storage.return_value
    assert provider.limiter == mock_strategy.return_value


async def test_allow_delegates_to_limiter_hit():
    """
    Unit Test: Verifies that the provider's `_allow` method correctly
    delegates the call to the underlying 'limits' strategy object.
    """
    # Arrange
    # Create a mock for the RateLimiter strategy object
    mock_limiter = AsyncMock()
    mock_limiter.hit.return_value = True  # Simulate an allowed request

    # Manually create the provider and inject the mocked limiter
    provider = LimitsRateLimiter(settings=RateLimiterSettings())
    provider.limiter = mock_limiter  # Replace the real limiter with our mock

    # Act
    result = await provider._allow("test_key", "10/minute")

    # Assert
    assert result is True
    # Verify that the 'hit' method was called on our mock
    mock_limiter.hit.assert_awaited_once()
