import asyncio
from unittest.mock import MagicMock, patch

import pytest

from nala.athomic.resilience.rate_limiter.service import RateLimiterService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def rate_limiter_service_integration():
    """
    Fixture to create a RateLimiterService with a mocked settings.
    """
    mock_settings_instance = MagicMock()
    mock_settings_instance.enabled = True
    mock_settings_instance.backend = "limits"
    mock_settings_instance.provider.storage_backend = "memory"
    mock_settings_instance.namespace = "ratelimit"

    mock_settings_instance.policies = {}
    mock_settings_instance.default_policy_limit = "3/second"

    with patch(
        "nala.athomic.resilience.rate_limiter.service.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value.resilience.rate_limiter = mock_settings_instance

        service = RateLimiterService()

        await service.provider.connect()
        await service.provider.wait_ready()

        yield service

        await service.provider.close()


async def test_service_with_local_provider_allows_and_blocks(
    rate_limiter_service_integration: RateLimiterService,
):
    """
    Test that the RateLimiterService allows requests up to the limit and blocks afterwards.
    This test checks the basic functionality of the rate limiter service.
    """
    service = rate_limiter_service_integration
    policy = "test_policy"
    key_parts = ["user", "123"]

    for _ in range(3):
        is_allowed = await service.check(policy, *key_parts)
        assert is_allowed is True

    is_allowed = await service.check(policy, *key_parts)
    assert is_allowed is False

    await asyncio.sleep(1)
    is_allowed = await service.check(policy, *key_parts)
    assert is_allowed is True
