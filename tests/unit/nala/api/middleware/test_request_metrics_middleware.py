import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from nala.api.middleware.request_metrics_middleware import RequestMetricsMiddleware
from nala.athomic.config import get_settings
from nala.athomic.observability.metrics.usage.base_metrics import (
    in_progress_requests,
    request_counter,
    request_duration,
)


@pytest.mark.asyncio
async def test_request_metrics_middleware(monkeypatch):
    settings = get_settings().observability
    monkeypatch.setattr(settings, "enabled", True)

    request_counter._metrics.clear()
    request_duration._metrics.clear()
    in_progress_requests._value.set(0)

    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware)

    @app.get("/ping")
    async def ping():
        return JSONResponse({"message": "pong"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as ac:
        response = await ac.get("/ping")

    assert response.status_code == 200

    count = request_counter.labels(
        method="GET", endpoint="/ping", status_code="200"
    )._value.get()
    duration = request_duration.labels(method="GET", endpoint="/ping")._sum.get()
    in_progress = in_progress_requests._value.get()

    assert count == 1
    assert duration > 0
    assert in_progress == 0
