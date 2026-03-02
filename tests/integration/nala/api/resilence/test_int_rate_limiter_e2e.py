from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from nala.athomic.resilience.rate_limiter import rate_limited
from nala.athomic.resilience.rate_limiter.exceptions import RateLimitExceeded
from nala.athomic.resilience.rate_limiter.service import RateLimiterService

app = FastAPI()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": exc.args[0]})


@app.get("/limited")
@rate_limited(policy="e2e_test_policy")
async def get_limited_resource():
    return {"message": "You shall pass!"}


@pytest.fixture
async def isolated_rate_limiter_service() -> AsyncGenerator[RateLimiterService, None]:
    """
    Fixture that prepares an isolated E2E environment for the @rate_limited decorator.
    - The RateLimiterService will create a REAL provider with in-memory storage.
    - We mock the 'settings' object to control the service's behavior.
    - We ensure the decorator uses this isolated service instance.
    """
    mock_settings_instance = MagicMock()
    mock_settings_instance.enabled = True
    mock_settings_instance.backend = "limits"
    mock_settings_instance.provider.storage_backend = "memory"
    mock_settings_instance.namespace = "ratelimit_e2e"

    def policies_get_side_effect(key, default):
        if key == "e2e_test_policy":
            return "2/second"
        return default

    mock_settings_instance.policies.get.side_effect = policies_get_side_effect
    mock_settings_instance.default_policy_limit = "1000/hour"

    with patch(
        "nala.athomic.resilience.rate_limiter.service.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value.resilience.rate_limiter = mock_settings_instance

        service = RateLimiterService()

        await service.provider.connect()
        await service.provider.wait_ready()

        with patch(
            "nala.athomic.resilience.rate_limiter.decorators.rate_limited.rate_limiter_service",
            service,
        ):
            yield service

    await service.provider.close()


@pytest.mark.asyncio
async def test_rate_limited_endpoint_returns_429_when_exceeded(
    isolated_rate_limiter_service: RateLimiterService,
):
    """
    E2E Test: Ensures that an endpoint decorated with @rate_limited
    returns status 429 (Too Many Requests) when the limit is exceeded.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as client:
        response1 = await client.get("/limited")
        assert response1.status_code == 200, f"First request failed: {response1.text}"

        response2 = await client.get("/limited")
        assert response2.status_code == 200, f"Second request failed: {response2.text}"

        response3 = await client.get("/limited")
        assert response3.status_code == 429
