from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from nala.athomic.config import get_settings

metrics_router = APIRouter()


@metrics_router.get("/metrics")
async def metrics() -> Response:
    settings = get_settings().observability
    if not settings.enabled:
        return Response(status_code=404)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
