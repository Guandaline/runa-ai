import pytest

from nala.athomic.ai.context.factory import TokenServiceFactory
from nala.athomic.ai.context.policies import TierBasedLimitPolicy
from nala.athomic.config.schemas.ai.context.context_settings import AIContextSettings
from nala.athomic.context import context_vars


@pytest.fixture
def robust_service():
    return TokenServiceFactory.create(settings=AIContextSettings())


@pytest.mark.asyncio
async def test_registry_regex_resolution(robust_service):
    """
    Verifies if the registry correctly matches model names using Regex.
    """
    # GPT-4 Turbo variants (128k)
    limit, _ = robust_service.registry.resolve("gpt-4-turbo-2024-04-09", 0, "")
    assert limit == 128000

    # GPT-4 Classic (8k)
    limit, _ = robust_service.registry.resolve("gpt-4-0613", 0, "")
    assert limit == 8192

    # Llama 3 (Defaults to safe 8k in our rules, though capable of more)
    limit, _ = robust_service.registry.resolve("llama3:8b", 0, "")
    assert limit == 8192


@pytest.mark.asyncio
async def test_policy_tier_enforcement(robust_service):
    """
    Verifies if the TierBasedLimitPolicy correctly caps the budget.
    """
    token = context_vars.set_role("free")

    try:
        # Policy: Free tier capped at 2000 tokens
        policy = TierBasedLimitPolicy(tier_limits={"free": 2000, "pro": 10000})
        robust_service.policies = [policy]

        # Request for a powerful model (128k physical limit)
        budget = robust_service.calculate_budget(
            model_name="gpt-4-turbo",
            system_prompt="System",
            user_query="Hello",
            max_output_tokens=100,
        )

        # Assertions
        assert budget.model_limit == 128000, "Physical limit should be preserved"

        # This will now pass because get_role() returns "free"
        assert (
            budget.effective_limit == 2000
        ), f"Effective limit should be capped by policy. Got {budget.effective_limit}"

        assert (
            budget.available_context_tokens <= 2000
        ), "Available tokens must respect the cap"

    finally:
        # Proper cleanup using the context var token
        if token:
            context_vars.reset_role(token)
        else:
            context_vars.set_role(None)


@pytest.mark.asyncio
async def test_token_counting_fallback():
    """
    Verifies graceful fallback for unknown encodings.
    """
    service = TokenServiceFactory.create()

    # Use a non-existent encoding
    count = service.count_tokens("Test Payload", encoding_name="unknown_encoding_X")

    # Should fallback to cl100k_base or char-estimation
    assert count > 0
