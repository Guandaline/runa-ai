import pytest
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.routing import APIRouter
from httpx import AsyncClient
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from nala.athomic.config import get_settings


@pytest.mark.asyncio
async def test_metrics_endpoint_enabled(monkeypatch):
    settings = get_settings().observability
    monkeypatch.setattr(settings, "enabled", True)

    router = APIRouter()

    @router.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(app=app, base_url="https://test") as ac:
        response = await ac.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    assert (
        b"secret_access_total" in response.content
        or b"api_requests_total" in response.content
    )


@pytest.mark.asyncio
async def test_metrics_endpoint_disabled(monkeypatch):
    settings = get_settings().observability
    monkeypatch.setattr(settings, "enable", False)

    router = APIRouter()

    @router.get("/metrics")
    async def metrics():
        if not settings.enabled:
            return Response(status_code=404)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(app=app, base_url="https://test") as ac:
        response = await ac.get("/metrics")

    assert response.status_code == 404
