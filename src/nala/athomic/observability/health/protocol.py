# src/nala/athomic/health/readiness/interfaces.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class ReadinessCheck(Protocol):
    """
    Defines the contract for an individual readiness check implementation.

    Any class that implements this protocol can be registered with the
    ReadinessRegistry to contribute to the overall application readiness state.
    """

    name: str
    """A unique, descriptive name for the check (e.g., 'database_connection')."""

    def enabled(self) -> bool:
        """
        Determines if the check should be executed based on configuration
        or runtime environment.

        Returns:
            bool: True if the check should run, False otherwise.
        """
        ...

    async def check(self) -> bool:
        """
        Performs the asynchronous check of the dependency or resource.

        This method must be lightweight and fast to avoid delaying the
        readiness probe.

        Returns:
            bool: True if the resource is healthy (ready), False otherwise.
        """
        ...
