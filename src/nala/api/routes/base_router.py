from time import time
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from nala.athomic.observability import get_logger
from nala.athomic.observability.metrics.usage import (
    api_route_request_duration_seconds,
    api_route_requests_total,
)

logger = get_logger(__name__)


class BaseRouter(APIRouter):
    """
    A custom router that uses AuthPolicyRoute by default, enabling
    security policies to be set directly on routes.
    """

    def __init__(
        self,
        prefix: Optional[str] = "",
        **kwargs,
    ) -> None:
        super().__init__(prefix=prefix, **kwargs)

    async def handle_request(self, func, *args, **kwargs) -> Any:
        """Generic method to catch exceptions and log errors."""
        start_time = time.monotonic()
        func_name = func.__name__
        status = "unknown"

        try:
            logger.debug(
                f"Handling request for {func.__name__} with args={args}, kwargs={kwargs}"
            )
            result = await func(*args, **kwargs)
            logger.debug(f"Request for {func.__name__} completed successfully")
            status = "success"
            return result
        except HTTPException as e:
            logger.warning(f"HTTPException in {func.__name__}: {e.detail}")
            status = "http_error"
            raise e
        except Exception as e:
            status = "error"
            logger.error(
                f"Unhandled exception in {func.__name__}: {str(e)}", exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
        finally:
            duration = time.monotonic() - start_time
            api_route_requests_total.labels(route_name=func_name, status=status).inc()
            api_route_request_duration_seconds.labels(route_name=func_name).observe(
                duration
            )
