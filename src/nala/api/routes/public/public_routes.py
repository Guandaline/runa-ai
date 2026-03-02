from ..base_router import BaseRouter
from .open_router import open_router

public_routes = BaseRouter(prefix="", tags=["Public"])


public_routes.include_router(open_router)
