from fastapi.params import Depends


from ..base_router import BaseRouter
from .health_router import health_router
from .metrics_router import metrics_router
from .readyz_router import readyz_router

internal_routes = BaseRouter(
    prefix="/internal",
    tags=["Internal"],
)

# Internal routes for monitoring and management

prefix_monitoring = ""

internal_routes.include_router(health_router, prefix=prefix_monitoring, tags=["Health"])
internal_routes.include_router(
    metrics_router, prefix=prefix_monitoring, tags=["Metrics"]
)
internal_routes.include_router(
    readyz_router, prefix=prefix_monitoring, tags=["Readiness"]
)
