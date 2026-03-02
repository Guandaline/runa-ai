"""Defines the unified Protocol for stateful, manageable services within the Nala framework.

Any class that implements this protocol is considered a "Service" and can be
managed by components that depend on this contract, regardless of its concrete
implementation.
"""

from typing import Any, Coroutine, Dict, Protocol, runtime_checkable


@runtime_checkable
class BaseServiceProtocol(Protocol):
    """Defines the public contract for a stateful, manageable service.

    This protocol unifies the concepts of connectable services (like a database
    client) and runnable services (like a background worker). Any class that
    adheres to this contract can be managed by the `LifecycleManager`, ensuring
    consistent startup, shutdown, and health checking across the framework.
    """

    async def start(self) -> Coroutine[Any, Any, None]:
        """Starts the service, handling connections and/or background tasks.

        This method should manage the transition from PENDING to READY or RUNNING.
        """
        ...

    async def stop(self) -> Coroutine[Any, Any, None]:
        """Stops the service gracefully, closing connections and cancelling background tasks.

        This method should manage the transition to the CLOSED state.
        """
        ...

    def is_enabled(self) -> bool:
        """Returns True if the service is enabled in the configuration."""
        ...

    def is_running(self) -> bool:
        """Returns True if the service's continuous background task (`_run_loop`) is currently active.

        For services without a background task, this can be an alias for `is_ready()`.
        """
        ...

    def is_ready(self) -> bool:
        """Returns True if the service is initialized, connected, and immediately ready for operations.

        This state is the primary target for readiness checks.
        """
        ...

    async def wait_ready(self) -> None:
        """Asynchronously blocks until the service becomes ready.

        This is the primary method used to manage dependencies between services during startup.
        """
        ...

    def is_closed(self) -> bool:
        """Returns True if the service has been permanently stopped and its resources released."""
        ...

    def connect(self) -> Coroutine[Any, Any, None]:
        """Alias for `start()`. Establishes a connection to the service."""
        ...

    def close(self) -> Coroutine[Any, Any, None]:
        """Alias for `stop()`. Closes the service connection."""
        ...

    def is_connected(self) -> bool:
        """Returns True if the service is currently connected and ready.

        Typically equivalent to `is_ready()`.
        """
        ...

    async def set_ready(self, ready: bool = True) -> None:
        """Sets the internal ready state of the service. Intended for implementers (BaseService subclasses).

        Args:
            ready (bool): The desired ready state.
        """
        ...

    async def set_running(self, running: bool = True) -> None:
        """Sets the internal running state of the service. Intended for implementers (BaseService subclasses).

        Args:
            running (bool): The desired running state.
        """
        ...

    def health(self) -> Dict[str, Any]:
        """Returns a dictionary with the service's current health and state, including basic status flags."""
        ...

    def health_extra(self) -> Dict[str, Any]:
        """Returns a dictionary with extra, service-specific health details (e.g., last connection time, queue depth)."""
        ...
