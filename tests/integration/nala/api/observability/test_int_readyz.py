import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from nala.api.routes.internal import readyz_router
from nala.athomic.observability.health.registry import (
    ReadinessCheck,
    readiness_registry,
)

TEST_URL = "https://test"


class AlwaysOkCheck(ReadinessCheck):
    name = "mock_ok"

    def enabled(self):
        return True

    async def check(self):
        return True


class AlwaysFailCheck(ReadinessCheck):
    name = "mock_fail"

    def enabled(self):
        return True

    async def check(self):
        return False


class SkippedCheck(ReadinessCheck):
    name = "mock_skipped"

    def enabled(self):
        return False

    async def check(self):
        return True  # won't be called


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readyz_all_ok():
    app = FastAPI()
    readiness_registry._checks.clear()
    readiness_registry.register(AlwaysOkCheck())
    app.include_router(readyz_router)

    async with AsyncClient(transport=ASGITransport(app), base_url=TEST_URL) as ac:
        res = await ac.get("/readyz")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["checks"]["mock_ok"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readyz_with_failure():
    app = FastAPI()
    readiness_registry._checks.clear()
    readiness_registry.register(AlwaysOkCheck())
    readiness_registry.register(AlwaysFailCheck())
    app.include_router(readyz_router)

    async with AsyncClient(transport=ASGITransport(app), base_url=TEST_URL) as ac:
        res = await ac.get("/readyz")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "unavailable"
        assert data["checks"]["mock_fail"] == "fail"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readyz_skipped():
    app = FastAPI()
    readiness_registry._checks.clear()
    readiness_registry.register(SkippedCheck())
    app.include_router(readyz_router)

    async with AsyncClient(transport=ASGITransport(app), base_url=TEST_URL) as ac:
        res = await ac.get("/readyz")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["checks"]["mock_skipped"] == "skipped"
