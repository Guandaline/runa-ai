# src/nala/athomic/resilience/locking/protocol.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Protocol, runtime_checkable


@runtime_checkable
class LockingProtocol(Protocol):
    """
    Defines the contract for a locking provider, abstracting the mechanism
    used to ensure mutual exclusion for shared resources.

    Implementations can be either **local (in-memory)** for single-process use
    or **distributed (e.g., Redis)** for microservices in a clustered environment.
    """

    @asynccontextmanager
    async def acquire(self, key: str, timeout: int = 30) -> AsyncGenerator[None, None]:
        """
        Acquires a lock for a specific key, intended for use with the `async with` statement.

        The operation blocks until the lock is acquired or the timeout is reached.

        Args:
            key (str): The unique resource identifier to be locked (e.g., "user:123").
            timeout (int): The maximum time (in seconds) to wait to acquire the lock.
                           Defaults to 30 seconds.

        Yields:
            None: Execution continues inside the block only if the lock is successfully acquired.

        Raises:
            asyncio.TimeoutError: If the lock cannot be acquired within the specified timeout.
        """
        # The `yield` is used as a placeholder in the Protocol definition
        # for methods intended to be context managers.
        yield
