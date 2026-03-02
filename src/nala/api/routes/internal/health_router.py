from typing import Any

import psutil
from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
async def health_check() -> dict[str, Any]:
    """Verifica se o serviço está rodando corretamente."""
    return {
        "status": "ok",
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
    }


@health_router.get("/healthz", tags=["infra"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
