# src/nala/athomic/database/factory.py

from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.database.database_config import DatabaseSettings
from nala.athomic.observability import get_logger

from .manager import ConnectionManager

logger = get_logger(__name__)


class ConnectionManagerFactory:
    """
    Manages the singleton instance of the ConnectionManager.
    Ensures that only one instance of the ConnectionManager exists throughout
    the application's lifecycle.
    """

    def __init__(self) -> None:
        self._instance: Optional[ConnectionManager] = None

    def create(
        self, settings: Optional[DatabaseSettings] = None
    ) -> ConnectionManager | None:
        """
        Creates and returns the singleton instance of the ConnectionManager.

        On the first call, it instantiates the ConnectionManager. Subsequent calls
        return the cached instance.
        """
        if self._instance is None:
            logger.debug("Creating a new ConnectionManager instance...")

            if settings is None:
                logger.warning("No database settings provided; using default settings.")
                app_settings = get_settings()
                settings = app_settings.database

            if not settings or not settings.enabled:
                logger.warning(
                    "DatabaseSettings are not provided or disabled; "
                    "the ConnectionManager will be created in a disabled state."
                )
                return None

            self._instance = ConnectionManager(settings=settings)

        return self._instance

    async def clear(self) -> None:
        """
        Clears the singleton instance of the ConnectionManager.
        This is primarily used for test isolation.
        """
        if self._instance is not None:
            if self._instance.is_ready():
                await self._instance.stop()
            self._instance = None


connection_manager_factory = ConnectionManagerFactory()
