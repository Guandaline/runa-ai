import time
from typing import Any, Callable, Generator, Optional

from _asyncio import Future
from starlette.middleware.base import BaseHTTPMiddleware, _StreamingResponse
from starlette.requests import Request
from starlette.responses import Response

from nala.athomic.config import get_settings
from nala.athomic.context.context_vars import get_trace_id
from nala.athomic.observability.metrics.usage.base_metrics import (
    in_progress_requests,
    request_counter,
    request_duration,
)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Generator[Optional[Future], None, _StreamingResponse]:
        settings = get_settings().observability
        if not settings.enabled:
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        in_progress_requests.inc()
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception:
            in_progress_requests.dec()
            raise

        trace_id = get_trace_id() 
        exemplar = {"TraceID": trace_id} if trace_id else None

        duration = time.perf_counter() - start_time

        request_counter.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()
        request_duration.labels(method=method, endpoint=endpoint).observe(
            duration, exemplar=exemplar
        )
        in_progress_requests.dec()

        return response
