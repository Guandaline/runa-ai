import asyncio
import os
import typing
from typing import AsyncGenerator

import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

import pytest
from httpx import ASGITransport, AsyncClient

from nala.athomic.config.settings import get_settings
from nala.athomic.resilience.rate_limiter.factory import RateLimiterFactory
from nala.athomic.resilience.rate_limiter.service import RateLimiterService


from nala.api.main import app


@pytest_asyncio.fixture(scope="function")
async def mongo_test_client():
    client = AsyncIOMotorClient(
        os.environ.get("MONGO_TEST_URI", "mongodb://localhost:27017/nala_test_db")
    )
    yield client
    client.close()


@pytest_asyncio.fixture(scope="function")
def memory_rate_limiter_service() -> typing.Generator[RateLimiterService, None, None]:
    """
    Fixture that provides a RateLimiterService configured with an in-memory
    provider for isolated integration testing.
    """
    # Force the factory to create a new instance for this test
    settings = get_settings()
    settings.resilience.rate_limiter.backend = "limits"
    settings.resilience.rate_limiter.provider.storage_backend = "memory"
    settings.resilience.rate_limiter.policies = {"test_policy": "3/second"}

    # Use the factory to create a real service with real (local) providers
    service = RateLimiterFactory.create(settings=settings.resilience.rate_limiter)

    # The BaseService needs to be "started"
    # In a real app, the lifespan manager does this. In tests, we do it manually.
    loop = asyncio.get_event_loop()
    loop.run_until_complete(service.start())

    yield service

    # Teardown
    loop.run_until_complete(service.stop())


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Defines the backend for anyio to ensure async tests run correctly.
    """
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides a high-level AsyncClient for integration testing.

    This fixture ensures that the FastAPI application is correctly
    wrapped in an ASGITransport, allowing for full-stack integration
    tests without a real network socket.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=True
    ) as ac:
        yield ac
