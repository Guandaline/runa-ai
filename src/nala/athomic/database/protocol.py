from typing import Any, Protocol

from nala.athomic.services.protocol import BaseServiceProtocol


class DatabaseClientProtocol(BaseServiceProtocol, Protocol):
    """
    Protocol for a document database provider.

    Defines the contract for managing a database connection and providing
    access to the native database instance (e.g., a Motor/Beanie database object).
    It inherits from ConnectionServiceProtocol to be managed by the application's lifecycle.
    """

    async def get_database(self) -> Any:
        """
        Returns the native database instance required by repositories
        to perform operations.
        """
        ...
