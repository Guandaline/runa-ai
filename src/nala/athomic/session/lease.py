from __future__ import annotations

import time
from typing import Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class SessionLease(Generic[T]):
    """
    Represents a leased, reusable resource with explicit lifecycle management.

    A SessionLease encapsulates:
    - A concrete resource instance.
    - Idle-based expiration logic (TTL).
    - Monotonic time tracking for safety against system clock changes.
    - Asynchronous, idempotent cleanup semantics.

    This class is intentionally domain-agnostic and does not assume any
    specific resource type. It is suitable for managing resources such as:
    sandboxes, database connections, HTTP clients, LLM sessions, or any
    other expensive or stateful object requiring controlled reuse.

    The lease itself contains no concurrency logic and no scheduling behavior.
    Those responsibilities are delegated to the SessionManager.
    """

    def __init__(
        self,
        resource: T,
        *,
        ttl_seconds: int,
        on_close: Optional[Callable[[T], Awaitable[None]]] = None,
    ) -> None:
        """
        Initialize a new SessionLease.

        Args:
            resource:
                The concrete resource instance being leased.
            ttl_seconds:
                The maximum allowed idle time in seconds before the lease
                is considered expired. Must be a positive integer.
            on_close:
                Optional asynchronous callback invoked exactly once when
                the lease is closed. This callback is responsible for
                releasing any underlying resources (I/O, processes, network
                connections, etc.).

        Raises:
            ValueError:
                If ttl_seconds is not a positive integer.
        """
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")

        now = time.monotonic()

        self._resource: T = resource
        self._ttl_seconds: int = ttl_seconds
        self._created_at: float = now
        self._last_used_at: float = now
        self._on_close: Optional[Callable[[T], Awaitable[None]]] = on_close
        self._closed: bool = False

    @property
    def resource(self) -> T:
        """
        Return the leased resource instance.

        The returned object is the same instance provided at creation time.
        """
        return self._resource

    @property
    def created_at(self) -> float:
        """
        Return the monotonic timestamp at which this lease was created.
        """
        return self._created_at

    @property
    def last_used_at(self) -> float:
        """
        Return the monotonic timestamp of the last recorded usage of the lease.
        """
        return self._last_used_at

    def touch(self) -> None:
        """
        Mark the lease as recently used.

        Updates the internal last-used timestamp to the current monotonic time.
        Calling this method on a closed lease is safe and has no effect.
        """
        if self._closed:
            return

        self._last_used_at = time.monotonic()

    def is_expired(self, now: float) -> bool:
        """
        Determine whether the lease has expired due to inactivity.

        Args:
            now:
                The current monotonic timestamp, typically obtained via
                time.monotonic() by the caller.

        Returns:
            True if the idle duration exceeds the configured TTL or if the
            lease has already been closed; False otherwise.
        """
        if self._closed:
            return True

        return (now - self._last_used_at) > self._ttl_seconds

    async def close(self) -> None:
        """
        Close the lease and release the underlying resource.

        This method is asynchronous to support cleanup operations that
        involve I/O (e.g., terminating processes, closing network connections).

        The method is idempotent:
        - Multiple calls are safe.
        - The cleanup callback is executed at most once.

        If no cleanup callback was provided, this method becomes a no-op.
        """
        if self._closed:
            return

        self._closed = True

        if self._on_close is not None:
            await self._on_close(self._resource)
