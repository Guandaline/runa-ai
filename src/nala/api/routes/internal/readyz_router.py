# nala/api/routes/readyz.py

from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from nala.athomic.observability.health.registry import readiness_registry

readyz_router = APIRouter()


@readyz_router.get("/readyz", tags=["infra"])
async def readyz() -> JSONResponse:
    results = await readiness_registry.run_all()

    # Resultado final da API depende se há alguma falha
    any_fail = any(status == "fail" for status in results.values())

    return JSONResponse(
        content={
            "status": "ok" if not any_fail else "unavailable",
            "checks": results,
        },
        status_code=(
            status.HTTP_200_OK if not any_fail else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )
