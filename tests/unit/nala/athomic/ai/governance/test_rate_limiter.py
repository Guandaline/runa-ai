from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nala.athomic.ai.governance.exceptions import QuotaExceededError
from nala.athomic.ai.governance.guards.rate_limiter import RateLimitGuard
from nala.athomic.context import context_var_manager, context_vars
from nala.athomic.resilience.rate_limiter.service import RateLimiterService


@pytest.fixture
def mock_rate_limiter_service() -> MagicMock:
    service = MagicMock(spec=RateLimiterService)
    service.check = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_rate_limiter_allows_request_under_limit(
    mock_rate_limiter_service: MagicMock,
) -> None:
    mock_rate_limiter_service.check.return_value = True
    guard = RateLimitGuard(policy_name="ai_default", service=mock_rate_limiter_service)

    token = context_vars.set_user_id("user_123")
    try:
        await guard.check("prompt")
    finally:
        context_var_manager.reset("user_id", token)

    mock_rate_limiter_service.check.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limiter_raises_quota_exceeded(
    mock_rate_limiter_service: MagicMock,
) -> None:
    mock_rate_limiter_service.check.return_value = False
    guard = RateLimitGuard(policy_name="ai_default", service=mock_rate_limiter_service)

    token = context_vars.set_user_id("user_123")
    try:
        with pytest.raises(QuotaExceededError) as exc_info:
            await guard.check("prompt")
    finally:
        context_var_manager.reset("user_id", token)

    assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rate_limiter_constructs_correct_key_from_context(
    mock_rate_limiter_service: MagicMock,
) -> None:
    """
    Verifies that global context variables are correctly picked up by the key generator.
    We must ensure multi-tenancy is enabled in settings for the generator to pick it up.
    """
    mock_rate_limiter_service.check.return_value = True

    mock_settings = MagicMock()
    mock_settings.context.multi_tenancy_enabled = True
    mock_settings.context.static_prefix = "nala"
    mock_settings.context.separator = ":"
    mock_settings.context.use_user_uid = True

    with patch(
        "nala.athomic.context.generator.get_settings", return_value=mock_settings
    ):
        guard = RateLimitGuard(
            policy_name="ai_premium", service=mock_rate_limiter_service
        )

    t_token = context_vars.set_tenant_id("tenant_XYZ")
    u_token = context_vars.set_user_id("user_ABC")

    try:
        await guard.check("prompt")
    finally:
        context_var_manager.reset("tenant_id", t_token)
        context_var_manager.reset("user_id", u_token)

    call_args = mock_rate_limiter_service.check.call_args
    assert call_args is not None

    generated_key = call_args.args[1]

    assert "tenant_XYZ" in generated_key
    assert "user_ABC" in generated_key
    assert "ai_premium" in generated_key


@pytest.mark.asyncio
async def test_rate_limiter_uses_ip_for_anonymous_user(
    mock_rate_limiter_service: MagicMock,
) -> None:
    """
    Verifies fallback to IP when user_id is missing.
    """
    mock_rate_limiter_service.check.return_value = True
    guard = RateLimitGuard(policy_name="ai_public", service=mock_rate_limiter_service)

    ip_token = context_vars.set_source_ip("192.168.1.1")
    u_token = context_vars.set_user_id(None)

    try:
        await guard.check("prompt")
    finally:
        context_var_manager.reset("source_ip", ip_token)
        context_var_manager.reset("user_id", u_token)

    call_args = mock_rate_limiter_service.check.call_args
    generated_key = call_args.args[1]

    assert "ip:192.168.1.1" in generated_key
