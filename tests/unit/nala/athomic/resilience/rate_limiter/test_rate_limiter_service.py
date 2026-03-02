# tests/unit/nala/athomic/resilience/rate_limiter/test_rate_limiter_service.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nala.athomic.resilience.rate_limiter.service import RateLimiterService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def rate_limiter_service():
    """
    Unified fixture that prepares the environment for all RateLimiterService tests.
    - Mocks all external dependencies.
    - Provides a mock 'settings' object that behaves like the real one.
    """
    mock_provider = AsyncMock()
    mock_provider.allow.return_value = True
    mock_provider.service_name = "mock_provider"

    with (
        patch(
            "nala.athomic.resilience.rate_limiter.service.get_settings"
        ) as mock_get_settings,
        patch(
            "nala.athomic.resilience.rate_limiter.service.RateLimiterFactory.create",
            return_value=mock_provider,
        ),
        patch(
            "nala.athomic.resilience.rate_limiter.service.ContextKeyGenerator"
        ) as mock_key_gen_class,
        patch(
            "nala.athomic.resilience.rate_limiter.service.rate_limiter_allowed_total"
        ) as mock_allowed_metric,
        patch(
            "nala.athomic.resilience.rate_limiter.service.rate_limiter_blocked_total"
        ) as mock_blocked_metric,
    ):
        # Configure the KeyGenerator mock
        mock_key_resolver_instance = MagicMock()

        def generate_side_effect(*args):
            key_parts = ":".join(map(str, args))
            return f"nala:ratelimit:{key_parts}"

        mock_key_resolver_instance.generate.side_effect = generate_side_effect
        mock_key_gen_class.return_value = mock_key_resolver_instance

        # Configure a realistic mock settings object
        mock_settings_instance = MagicMock()
        mock_settings_instance.enabled = True
        mock_settings_instance.namespace = "ratelimit"
        # Most important: .policies is a real dict and .default_policy_limit is a real string
        mock_settings_instance.policies = {
            "heavy": "1000/hour",
            "no_limit_policy": "nolimit",
        }
        mock_settings_instance.default_policy_limit = "100/hour"

        # The get_settings mock returns an object containing our mock settings
        mock_get_settings.return_value.resilience.rate_limiter = mock_settings_instance

        # Instantiate the service to be tested
        service = RateLimiterService()

        yield (
            service,
            {
                "provider": mock_provider,
                "settings": mock_settings_instance,
                "allowed_metric": mock_allowed_metric,
                "blocked_metric": mock_blocked_metric,
            },
        )


# --- Test Cases Focused on Service Logic ---


async def test_check_allowed_uses_specific_policy(rate_limiter_service):
    """Checks if the service uses the specific policy from the policies dict."""
    service, mocks = rate_limiter_service
    mocks["provider"].allow.return_value = True

    is_allowed = await service.check("heavy", "test_user")

    assert is_allowed is True
    # Checks if the provider was called with the 'heavy' policy limit
    mocks["provider"].allow.assert_awaited_once_with(
        "nala:ratelimit:heavy:test_user", "1000/hour", "heavy"
    )
    mocks["allowed_metric"].labels.return_value.inc.assert_called_once()


async def test_check_blocked(rate_limiter_service):
    """Checks the blocked path and the correct metric."""
    service, mocks = rate_limiter_service
    mocks["provider"].allow.return_value = False

    is_allowed = await service.check("heavy", "test_user")

    assert is_allowed is False
    mocks["provider"].allow.assert_awaited_once_with(
        "nala:ratelimit:heavy:test_user", "1000/hour", "heavy"
    )
    mocks["blocked_metric"].labels.return_value.inc.assert_called_once()


async def test_check_uses_default_limit_when_policy_not_found(rate_limiter_service):
    """Checks if the service uses default_policy_limit as a fallback."""
    service, mocks = rate_limiter_service

    await service.check("non_existent_policy", "test_user")

    # Checks if the provider was called with the DEFAULT limit from the settings object
    mocks["provider"].allow.assert_awaited_once_with(
        "nala:ratelimit:non_existent_policy:test_user",
        "100/hour",
        "non_existent_policy",
    )


async def test_check_returns_true_for_nolimit_policy(rate_limiter_service):
    """Checks if the 'nolimit' policy returns True immediately without calling the provider."""
    service, mocks = rate_limiter_service

    is_allowed = await service.check("no_limit_policy", "test_user")

    assert is_allowed is True
    # The provider should not be called, as the logic for 'nolimit' is a shortcut
    mocks["provider"].allow.assert_not_awaited()


async def test_check_returns_true_when_service_is_disabled(rate_limiter_service):
    """Checks if the service returns True immediately when it is disabled."""
    service, mocks = rate_limiter_service
    # Disable the service via the mock settings
    mocks["settings"].enabled = False

    is_allowed = await service.check("any_policy", "any_user")

    assert is_allowed is True
    mocks["provider"].allow.assert_not_awaited()
