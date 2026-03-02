# src/nala/athomic/database/manager.py

import asyncio
from typing import List, Optional, Union

from nala.athomic.config.schemas.database.database_config import DatabaseSettings
from nala.athomic.observability import get_logger
from nala.athomic.services import BaseService, BaseServiceProtocol

from .kvstore.manager import KVStoreManager
from .kvstore.protocol import KVStoreProtocol

logger = get_logger(__name__)

database_types = Union[KVStoreProtocol]  # Extend this Union as more database types are added

class ConnectionManager(BaseService):
    """
    Orchestrates the lifecycle of all database connection managers.
    Acts as a Facade to access different types of database connections, delegating
    the responsibility to specialized managers.
    """

    def __init__(self, settings: DatabaseSettings):
        super().__init__(service_name="database_connection_manager")

        if settings is None:
            raise ValueError(
                "DatabaseSettings must be provided to initialize ConnectionManager."
            )

        self.managed_services: List[BaseServiceProtocol] = []
        self._kv_store_manager: Optional[KVStoreManager] = None

        if settings.kvstore:
            self._kv_store_manager = KVStoreManager(settings)
            self.managed_services.append(self._kv_store_manager)
        else:
            logger.info(
                "No [database.kvstore] config found. KVStoreManager will be disabled."
            )


        self._connection_getters = {
            "kv_store": self.get_kv_store,
        }

    async def _connect(self) -> None:
        """Starts all managed database managers concurrently."""
        if not self.managed_services:
            logger.info(f"No database managers to connect for '{self.service_name}'.")
            return

        connect_tasks = [manager.connect() for manager in self.managed_services]
        await asyncio.gather(*connect_tasks)

    async def _run_loop(self) -> None:
        """Waits for all subordinate manager loops to complete."""
        if not self.managed_services:
            return

        ready_tasks = [s.wait_ready() for s in self.managed_services if s.is_running()]
        if ready_tasks:
            await asyncio.gather(*ready_tasks, return_exceptions=True)

        run_tasks = [
            asyncio.create_task(s._run_loop())
            for s in self.managed_services
            if hasattr(s, "_run_loop") and s.is_ready()
        ]

        if run_tasks:
            self.logger.info(
                f"Starting main loop for {len(run_tasks)} database manager(s)..."
            )
            await asyncio.gather(*run_tasks)
        else:
            self.logger.warning(
                f"No ready database manager run loops to start for '{self.service_name}'."
            )

    async def _close(self) -> None:
        """Stops all managed database managers concurrently."""
        if not self.managed_services:
            return

        logger.info(f"Stopping {len(self.managed_services)} database manager(s)...")
        # Call stop() which is the public method on BaseService
        close_tasks = [manager.stop() for manager in self.managed_services]
        await asyncio.gather(*close_tasks, return_exceptions=True)
        logger.info("All database managers stopped.")

    def get(self, connection_type: str, name: Optional[str] = None) -> database_types:
        """
        Generic retriever for any database connection type using O(1) dispatch.

        Args:
            connection_type: 'kv_store', 'document', 'vector', or 'graph'.
            name: The specific connection name (optional, defaults to config default).

        Returns:
            The requested database client/protocol.

        Raises:
            ValueError: If the connection type is unknown.
            RuntimeError: If the requested manager is disabled.
        """
        # Retrieve the bound method from the map
        getter = self._connection_getters.get(connection_type)

        if not getter:
            valid_types = list(self._connection_getters.keys())
            raise ValueError(
                f"Unknown connection type: '{connection_type}'. "
                f"Valid types are: {valid_types}"
            )

        # Execute the retrieved method
        return getter(name)

    def get_kv_store(self, name: Optional[str] = None) -> KVStoreProtocol:
        """
        Delegates the call to the K/V store manager.
        """
        if not self._kv_store_manager:
            raise RuntimeError(
                "KVStore service was not configured. "
                "Ensure [database.kvstore] settings are provided."
            )
        return self._kv_store_manager.get_client(name)