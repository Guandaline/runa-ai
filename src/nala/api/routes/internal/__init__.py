# routes/internal/__init__.py
from .health_router import health_router
from .internal_routes import internal_routes
from .metrics_router import metrics_router
from .readyz_router import readyz_router

__all__ = [
    "internal_routes",
    "health_router",
    "metrics_router",
    "readyz_router",
]
