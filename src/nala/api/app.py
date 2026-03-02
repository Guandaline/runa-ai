from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles

from nala.api.exceptions import exception_handler
from nala.api.startup.domain_initializers import register_api_domain_initializers
from nala.api.startup.setup import setup_static_app_components
from nala.athomic.config import get_settings
from nala.athomic.facade import Athomic
from nala.athomic.observability import get_logger
from nala.athomic.performance.bootstrap import install_uvloop_if_available
from nala.athomic.provider import set_athomic_instance

settings = get_settings()

logger = get_logger(__name__)

app: Optional[FastAPI] = None


def create_app() -> FastAPI:
    """
    Application Factory: Creates, configures and defines the application lifecycle.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """
        Manages the application's lifespan by delegating entirely to the Athomic Facade.
        """
        logger.info("Starting FastAPI application lifespan...")

        athomic = Athomic(
            domain_initializers_registrar=register_api_domain_initializers
        )

        set_athomic_instance(athomic)
        app.state.athomic = athomic
        await athomic.startup()

        logger.info("FastAPI application lifespan started.")

        yield

        await athomic.shutdown()

    install_uvloop_if_available()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    setup_static_app_components(app)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> None:
        return exception_handler.http_exception_handler(request, exc)

    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> FileResponse:
        return FileResponse("static/favicon.ico")

    @app.get("/")
    async def root(request: Request) -> dict:
        language = getattr(request.state, "language", "default")
        return {"message": f"Hello World! In language: {language}"}

    return app


def get_app() -> FastAPI:
    """
    Returns the FastAPI application instance.
    If it doesn't exist, creates a new one.
    """
    global app
    if app is None:
        app = create_app()
    return app
