import asyncio
from typing import Any, Dict, Optional

from nala.athomic.observability.log import Logger, get_logger
from nala.athomic.observability.metrics.usage.service_lifecycle_metrics import (
    service_connection_attempts_total,
    service_connection_failures_total,
    service_connection_status,
    service_readiness_status,
)
from nala.athomic.observability.tracing.tracing import get_tracer

from .enums import ServiceState
from .exceptions import (
    ServiceAlreadyRunningError,
    ServiceConnectionError,
    ServiceUnavailableError,
)
from .protocol import BaseServiceProtocol


class BaseService(BaseServiceProtocol):
    """Abstract base class for stateful, lifecycle-managed services (Template Method Pattern).

    This class provides a complete, thread-safe and asynchronous lifecycle for components
    that need to manage external resources or run background tasks. It centralizes:
    1. **State Management:** Tracking status (PENDING, READY, RUNNING, CLOSED).
    2. **Orchestration:** Idempotent, ordered startup (`connect`) and shutdown (`close`).
    3. **Observability:** Integration with metrics (connection status, readiness status)
       and tracing (OpenTelemetry).

    Subclasses must provide their specific behavior by implementing the template methods
    `_connect`, `_close`, and optionally `_run_loop`.

    Attributes:
        service_name (str): A unique identifier for the service, used in logs and metrics.
        logger (Logger): A pre-configured logger instance for the service.
        tracer (Tracer): An OpenTelemetry tracer instance for the service.
    """

    service_name: str
    logger: Logger

    def __init__(
        self,
        service_name: str,
        enabled: Optional[bool] = True,
    ) -> None:
        """Initializes the BaseService.

        Args:
            service_name (str): The unique identifier for this service instance.
            enabled (Optional[bool]): If False, the service's lifecycle methods
                (start, stop) will be skipped.
        """
        self.service_name = service_name
        self.logger: Logger = get_logger(self.service_name)
        self.tracer = get_tracer(self.service_name)
        self._enabled = enabled

        self._lock = asyncio.Lock()
        self._ready = asyncio.Event()
        self._state = ServiceState.PENDING
        self._is_closed = False

        self._run_task: Optional[asyncio.Task] = None
        self._last_start_error: Optional[str] = None

        # Initialize Prometheus Gauges to a default state (0 or disconnected/not ready)
        service_connection_status.labels(service=self.service_name).set(0)
        service_readiness_status.labels(service=self.service_name).set(0)

    async def _connect(self) -> None:
        """Template Method: Establishes network connections, configures client, etc.

        Subclasses must implement this to define their connection-specific logic.
        This method is called during `connect()`.
        """
        pass

    async def _close(self) -> None:
        """Template Method: Cleans up network connections, resources, or internal state.

        Subclasses must implement this to define their cleanup logic.
        This method is called during `close()`/`stop()`.
        """
        pass

    async def _run_loop(self) -> None:
        """Template Method: The indefinite background task (poller, consumer, heartbeat).

        Subclasses that require a continuous background process must implement this.
        It is automatically started as an `asyncio.Task` during `connect()` if implemented.
        """
        pass

    async def start(self) -> None:
        """Starts the service, initiating the connection and optionally the background loop (alias for `connect()`)."""
        await self.connect()

    async def stop(self) -> None:
        """Stops the service gracefully, closing all connections and cancelling background tasks (alias for `close()`)."""
        await self.close()

    def _should_skip_connect(self) -> bool:
        """Checks if the connection flow should be skipped due to configuration or current state."""
        if not self._enabled:
            self.logger.debug(
                f"Connection skipped: service '{self.service_name}' is disabled."
            )
            return True

        if self._is_closed:
            raise ServiceAlreadyRunningError(self.service_name)

        return False

    async def _execute_connection_flow(self) -> None:
        """Orchestrates the ordered sequence of connection: hooks, _connect, task start, and readiness signal."""
        self.logger.info(f"Connecting to service '{self.service_name}'...")

        await self.before_start()
        await self._connect()

        # Check if the subclass implemented its own _run_loop beyond the empty BaseService one
        run_loop_impl = getattr(self._run_loop, "__func__", self._run_loop)
        base_run_loop_impl = getattr(
            BaseService._run_loop, "__func__", BaseService._run_loop
        )

        if run_loop_impl is not base_run_loop_impl:
            self._run_task = asyncio.create_task(
                self._run_loop(), name=f"{self.service_name}_run_loop"
            )
            self._state = ServiceState.RUNNING
        else:
            self._state = ServiceState.READY

        # Update metrics to indicate connection success
        service_connection_status.labels(service=self.service_name).set(1)

        if not self._ready.is_set():
            await self.set_ready()
            self.logger.success(f"Service '{self.service_name}' is now READY.")

        await self.after_start()
        self.logger.success(f"Successfully started service '{self.service_name}'.")

    def _handle_connection_failure(self, exc: Exception) -> None:
        """Centralized logic for handling connection failures, updating state, logging, and metrics."""
        self._state = ServiceState.FAILED
        self._last_start_error = f"{type(exc).__name__}: {exc}"
        service_connection_status.labels(service=self.service_name).set(0)
        service_connection_failures_total.labels(service=self.service_name).inc()

        self.logger.exception(f"Failed to connect/start service '{self.service_name}'.")

        raise ServiceConnectionError(
            f"Connection to '{self.service_name}' failed."
        ) from exc

    async def connect(self) -> None:
        """Orchestrates the service connection and startup process.

        This method is idempotent, thread-safe (via `_lock`), and manages state
        transitions and failure mapping.
        """
        if self._should_skip_connect():
            self.logger.info(
                f"Service '{self.service_name}' is disabled; skipping connection."
            )
            if not self._enabled:
                # If disabled, immediately mark as ready to avoid blocking dependencies
                await self.set_ready()
            return

        async with self._lock:
            if self.is_running() or self._state in (
                ServiceState.CONNECTING,
                ServiceState.READY,
            ):
                return

            self.logger.info(f"Connecting to service '{self.service_name}'...")
            service_connection_attempts_total.labels(service=self.service_name).inc()
            self._state = ServiceState.CONNECTING

            try:
                self.logger.debug(
                    f"Starting connection flow for service '{self.service_name}'..."
                )
                await self._execute_connection_flow()
                self.logger.debug(
                    f"Connection flow for service '{self.service_name}' completed."
                )
            except Exception as exc:
                self.logger.error(
                    f"An error occurred while connecting to service '{self.service_name}': {exc}"
                )
                self._handle_connection_failure(exc)

    async def close(self) -> None:
        """Safely and permanently stops the service and cleans up resources.

        This method cancels the background task, executes the `_close` template
        method, and sets the final state to `CLOSED`.
        """
        async with self._lock:
            if self._is_closed:
                self.logger.debug(
                    f"Service '{self.service_name}' is already closed. Skipping close."
                )
                return

            await self.before_stop()

            self.logger.info(f"Closing connection to '{self.service_name}'...")

            if self._run_task and not self._run_task.done():
                self._run_task.cancel()
                try:
                    await self._run_task
                except (Exception, asyncio.CancelledError):
                    # Swallow exceptions/cancellation of the run task
                    pass
                finally:
                    self._run_task = None

            try:
                # Enforce a short timeout for the subclass's cleanup logic
                await asyncio.wait_for(self._close(), timeout=10.0)
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Service '{self.service_name}' task did not stop within 10.0s."
                )
            except Exception as e:
                self.logger.exception(
                    f"An error occurred while closing the service '{self.service_name}': {e}"
                )
            finally:
                self._is_closed = True
                self._state = ServiceState.CLOSED
                # Update metrics to reflect final closed/disconnected state
                service_connection_status.labels(service=self.service_name).set(0)
                self.logger.success(
                    f"Successfully closed service '{self.service_name}'."
                )
                await self.after_stop()

    def is_enabled(self) -> bool:
        """Checks if the service is enabled in the configuration (Public Contract)."""
        return self._enabled

    def is_running(self) -> bool:
        """
        Returns True if the service has an active background task running.

        A service may be READY without being RUNNING (e.g. stateless clients).
        """
        return self._run_task is not None and not self._run_task.done()

    def is_ready(self) -> bool:
        """Returns True if the service is connected and ready for operations (Public Contract)."""
        return self._ready.is_set()

    async def wait_ready(self) -> None:
        """Blocks execution until the service becomes ready (Public Contract).

        Raises:
            ServiceUnavailableError: If the service failed during its startup.
        """
        if self._is_closed:
            raise ServiceUnavailableError(
                f"The service '{self.service_name}' is already closed."
            )

        if self._state == ServiceState.FAILED:
            raise ServiceUnavailableError(
                f"The service '{self.service_name}' failed to start previously."
            )
        try:
            self.logger.debug(
                f"Waiting for service '{self.service_name}' to be ready..."
            )
            await self._ready.wait()
        except Exception as e:
            self.logger.error(f"Error waiting for service '{self.service_name}': {e}")
            self._state = ServiceState.FAILED
            raise ServiceUnavailableError(
                f"Error waiting for '{self.service_name}'."
            ) from e

    async def set_ready(self, ready: bool = True) -> None:
        """Sets the internal ready state of the service.

        This signals to other components (via `wait_ready`) that the service
        is available for use. This method updates the internal state and Prometheus metrics.

        Args:
            ready (bool): The new ready state.
        """
        self.logger.debug(
            f"Setting service '{self.service_name}' ready state to {ready}."
        )
        if ready:
            if not self._ready.is_set():
                self._ready.set()
                self._state = ServiceState.READY
                service_readiness_status.labels(service=self.service_name).set(1)
                self.logger.info(f"Service '{self.service_name}' is now READY.")
        else:
            if self._ready.is_set():
                self._ready.clear()
                service_readiness_status.labels(service=self.service_name).set(0)
                self.logger.warning(f"Service '{self.service_name}' is now NOT READY.")

    async def set_not_ready(self) -> None:
        """Sets the service to a not-ready state."""
        await self.set_ready(False)

    async def before_start(self) -> None:
        """Lifecycle Hook: Executed before the main `_connect` call."""
        pass

    async def after_start(self) -> None:
        """Lifecycle Hook: Executed after the service has successfully started."""
        pass

    async def before_stop(self) -> None:
        """Lifecycle Hook: Executed before the main `_close` call, typically used to stop accepting new requests."""
        await self.set_ready(False)

    async def after_stop(self) -> None:
        """Lifecycle Hook: Executed after the service has been closed."""
        pass

    def is_connected(self) -> bool:
        """
        Returns True if the service successfully completed its connection phase
        and has not been closed.
        """
        return (
            self._state in (ServiceState.READY, ServiceState.RUNNING)
            and not self._is_closed
        )

    def is_closed(self) -> bool:
        """Checks if the service has been permanently closed (Public Contract)."""
        return self._is_closed

    def health_extra(self) -> Dict[str, Any]:
        """Provides a hook for subclasses to add service-specific health details (Public Contract)."""
        return {}

    def health(self) -> Dict[str, Any]:
        """Returns a dictionary with the current health and state of the service (Public Contract)."""
        return {
            "service_name": self.service_name,
            "enabled": self.is_enabled(),
            "state": self._state.name,
            "connected": self.is_connected(),
            "ready": self.is_ready(),
            "running": self.is_running(),
            "closed": self.is_closed(),
            "last_start_error": self._last_start_error,
            "extra": self.health_extra(),
        }
