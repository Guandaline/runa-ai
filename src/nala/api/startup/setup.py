# src/nala/api/startup/setup_app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from nala.api.middleware.request_context_middleware import RequestContextMiddleware
from nala.api.routes import internal_routes, public_routes
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


def setup_middlewares(app: FastAPI) -> None:
    """Adds all middlewares to the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)


def setup_base_routes(app: FastAPI) -> None:
    """Includes the application's base routes (DOES NOT include plugin routes)."""
    app.include_router(internal_routes)
    app.include_router(public_routes)


def setup_metrics(app: FastAPI) -> None:
    """Configures the Prometheus metrics instrumentator."""
    Instrumentator(
        should_group_status_codes=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/internal/metrics"],
    ).instrument(app).expose(app, endpoint="/internal/metrics", include_in_schema=False)


def setup_static_app_components(app: FastAPI) -> None:
    """
    Configures all static application components that do not depend
    on the lifespan to be initialized.
    """
    setup_middlewares(app)
    setup_base_routes(app)
    setup_metrics(app)
