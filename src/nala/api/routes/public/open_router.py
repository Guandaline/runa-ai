from typing import Any

from ..base_router import BaseRouter

open_router = BaseRouter(
    tags=["Open"],
)


@open_router.get("/open", summary="Documentation")
async def get_docs() -> Any:
    """Get the API documentation."""
    return {"docs": "https://github.com/nalaminds/nala-core-api"}
