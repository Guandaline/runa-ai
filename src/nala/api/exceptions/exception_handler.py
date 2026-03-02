from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handles HTTPExceptions, attempting to translate the error detail using
    internationalized messages if they are available on the request state.
    If not, it safely falls back to using the raw exception detail.
    """

    messages = getattr(request.state, "messages", {})

    error_message = messages.get(exc.detail, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": error_message},
        headers=exc.headers,
    )
