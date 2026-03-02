import asyncio
import time
from typing import Awaitable, Callable, Dict, Generic, Optional, TypeVar

from nala.athomic.observability import get_logger
from nala.athomic.session.lease import SessionLease

logger = get_logger(__name__)

T = TypeVar("T")


class SessionManager(Generic[T]):
    """
    Orchestrates the lifecycle of multiple session leases in a concurrency-safe manner.

    The SessionManager is responsible for:
    - Coordinating concurrent access to session resources.
    - Reusing active sessions when possible.
    - Enforcing idle-based expiration (TTL).
    - Performing lazy and explicit garbage collection.
    - Ensuring correct asynchronous cleanup of expired or terminated sessions.

    This manager is intentionally stateless with respect to configuration.
    Factories, TTL values, and cleanup callbacks are provided at acquisition
    time, enabling maximum flexibility and inversion of control.

    The manager does not perform background scheduling by default.
    Garbage collection may be triggered explicitly or integrated with an
    external scheduler if desired.
    """

    def __init__(self) -> None:
        """
        Initialize an empty SessionManager.

        No configuration or factories are bound at construction time.
        """
        self._sessions: Dict[str, SessionLease[T]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_or_create(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        ttl_seconds: int,
        on_close: Optional[Callable[[T], Awaitable[None]]] = None,
    ) -> SessionLease[T]:
        """
        Retrieve an existing active session or create a new one.

        This method guarantees that at most one resource instance is created
        concurrently per key. If a valid, non-expired session already exists,
        it is reused and marked as recently used.

        Args:
            key:
                Unique identifier for the session context (e.g., agent thread ID).
            factory:
                Asynchronous callable responsible for creating a new resource
                instance when needed.
            ttl_seconds:
                Idle timeout duration applied to the created session.
            on_close:
                Optional asynchronous callback used to clean up the resource
                when the session expires or is terminated.

        Returns:
            A SessionLease instance representing the active session.
        """
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            key_lock = self._locks[key]

        async with key_lock:
            now = time.monotonic()
            lease = self._sessions.get(key)

            if lease:
                if not lease.is_expired(now):
                    lease.touch()
                    return lease

                logger.info(f"Session '{key}' expired (lazy GC). Closing.")
                await lease.close()
                self._sessions.pop(key, None)

            try:
                resource = await factory()
            except Exception as exc:
                logger.error(f"Factory failed for session '{key}': {exc}")
                raise

            new_lease = SessionLease(
                resource,
                ttl_seconds=ttl_seconds,
                on_close=on_close,
            )

            self._sessions[key] = new_lease
            return new_lease

    async def terminate(self, key: str) -> None:
        """
        Forcefully terminate a session identified by the given key.

        If the session exists, it is closed and removed immediately.
        If no session exists for the key, the method returns silently.
        """
        async with self._global_lock:
            key_lock = self._locks.get(key)

        if not key_lock:
            return

        async with key_lock:
            lease = self._sessions.pop(key, None)
            if lease:
                await lease.close()
                logger.info(f"Session '{key}' terminated manually.")

    async def cleanup_expired(self) -> None:
        """
        Perform garbage collection of all expired sessions.

        This method scans all known sessions and closes those whose TTL
        has elapsed. It is safe to call concurrently with get_or_create
        and terminate operations.

        Intended to be called explicitly or by an external scheduler.
        """
        now = time.monotonic()

        async with self._global_lock:
            keys = list(self._sessions.keys())

        for key in keys:
            lock = self._locks.get(key)
            if not lock:
                continue

            async with lock:
                lease = self._sessions.get(key)
                if lease and lease.is_expired(now):
                    await lease.close()
                    self._sessions.pop(key, None)
                    logger.debug(f"Session '{key}' cleaned up by GC.")

    async def shutdown(self) -> None:
        """
        Gracefully terminate all active sessions.

        This method is intended to be invoked during application shutdown
        to ensure all managed resources are released cleanly.
        """
        logger.info("Shutting down SessionManager...")

        async with self._global_lock:
            keys = list(self._sessions.keys())

        for key in keys:
            await self.terminate(key)
