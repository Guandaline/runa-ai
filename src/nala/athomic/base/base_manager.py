import asyncio
from abc import ABCMeta
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from nala.athomic.base.factory import FactoryProtocol
from nala.athomic.config.schemas.base_settings import ConnectionGroupSettings
from nala.athomic.resilience.orchestrator import ResilienceOrchestrator
from nala.athomic.services import BaseService, BaseServiceProtocol

ClientProtocolT = TypeVar("ClientProtocolT", bound=BaseServiceProtocol)
ClientSettingsT = TypeVar("ClientSettingsT")


class BaseManager(
    BaseService, Generic[ClientProtocolT, ClientSettingsT], metaclass=ABCMeta
):
    """
    A generic, abstract lifecycle manager for multiple named instances of a client type.

    This abstract class provides the common logic for managing a collection of
    clients (BaseServiceProtocol instances) by:
    - Providing a hook `before_start` for subclasses to build client instances.
    - Orchestrating the lifecycle (connecting, running, and closing) of all
      managed clients.
    - Providing access to a specific client by name or to a default client.

    Subclasses MUST set `self.factory` in their `__init__`.
    Subclasses CAN override `before_start` for complex build logic.
    """

    def __init__(
        self,
        service_name: str,
        settings: ConnectionGroupSettings[ClientSettingsT],
        resilience_service: Optional[ResilienceOrchestrator] = None,
    ):
        """
        Initializes the generic manager.

        Args:
            service_name: The name of the service for logging and metrics.
            settings: A Pydantic model conforming to ConnectionGroupSettings,
                      containing the client configurations.
            resilience_service: An optional ResilienceOrchestrator instance
                                 for managing startup resilience.
        """
        super().__init__(service_name=service_name)

        self._resilience = resilience_service
        self._resilience_required: bool = resilience_service is not None

        if settings is None:
            # Handle cases where settings might be missing (e.g., disabled module)
            self.logger.warning(
                f"No settings provided for '{service_name}', manager will be inert."
            )
            self.settings = ConnectionGroupSettings[ClientSettingsT]()
        else:
            self.settings = settings

        self._managed_clients: Dict[str, ClientProtocolT] = {}
        self.managed_services: List[BaseServiceProtocol] = []
        # Subclasses MUST set this factory instance in their __init__
        self.factory: Optional[
            Type[FactoryProtocol[ClientProtocolT, ClientSettingsT]]
        ] = None

    def _resolve_active_configs(self) -> List[ClientSettingsT]:
        """Returns a list of all active client configurations."""
        active_settings = []
        if not self.settings or not self.settings.connections:
            return []

        for name, conn_settings in self.settings.connections.items():
            if getattr(conn_settings, "enabled", True):
                # Inject the connection name into the settings object
                setattr(conn_settings, "connection_name", name)
                active_settings.append(conn_settings)
        return active_settings

    async def before_start(self) -> None:
        """
        Default implementation for building and registering clients.

        This method provides a generic 1:1 mapping of connection settings
        to client instances using the provided `self.factory`.

        Subclasses with more complex logic (e.g., conditional creation)
        should override this method.
        """
        self.logger.debug(f"[{self.service_name}] Clearing existing client lists.")
        self._managed_clients.clear()
        self.managed_services.clear()

        if not self.factory:
            raise NotImplementedError(
                f"Manager '{self.service_name}' did not set 'self.factory' in its __init__."
            )

        client_settings: List[ClientSettingsT] = self._resolve_active_configs()

        if not client_settings:
            self.logger.info(f"No active connections found for '{self.service_name}'.")
            return

        for settings in client_settings:
            connection_name = getattr(settings, "connection_name")
            self.logger.debug(
                f"Creating client for connection: '{connection_name}' using {self.factory.__name__}"
            )
            instance = self.factory.create(settings=settings)

            is_default = connection_name == self.settings.default_connection_name
            if is_default:
                self.logger.debug(
                    f"Connection '{connection_name}' set as default for {self.service_name}."
                )

            self._register_client(name=connection_name, instance=instance)

    def _register_client(self, name: str, instance: ClientProtocolT) -> None:
        """Registers a client instance to be managed by this manager."""
        if name in self._managed_clients:
            self.logger.warning(
                f"Client '{name}' is being overwritten in {self.service_name}."
            )

        self._managed_clients[name] = instance
        self.managed_services.append(instance)
        self.logger.debug(f"Client '{name}' registered in {self.service_name}.")

    async def _connect_once(self) -> None:
        """
        Executes a single startup attempt for all managed services.

        This method must be executed inside a resilience boundary.
        It enforces all-or-nothing startup semantics and performs rollback
        if any managed service fails to connect or reach the READY state.
        """
        connected: List[BaseServiceProtocol] = []

        try:
            for client in self.managed_services:
                await client.connect()
                connected.append(client)

            await asyncio.gather(
                *(
                    client.wait_ready()
                    for client in connected
                    if hasattr(client, "wait_ready")
                )
            )

        except Exception:
            self.logger.exception(
                f"Startup failed for '{self.service_name}', rolling back."
            )
            for client in reversed(connected):
                try:
                    await client.stop()
                except Exception:
                    self.logger.exception(
                        f"Error while rolling back client '{client}'."
                    )
            raise

    async def _connect(self) -> None:
        """
        Connects all managed clients and waits until they reach the READY state.

        Retry, timeout and circuit breaker semantics are delegated to the
        resilience module.
        """
        if not self.managed_services:
            self.logger.info(
                f"No active services to connect for '{self.service_name}'."
            )
            return

        if self._resilience_required:
            if not self._resilience:
                raise RuntimeError(
                    f"{self.__class__.__name__} requires a resilience service to be injected."
                )

            await self._resilience.execute(
                operation_name=f"{self.service_name}.startup",
                func=self._connect_once,
            )
        else:
            await self._connect_once()

        self.logger.success(
            f"All {len(self.managed_services)} services for '{self.service_name}' connected."
        )

    async def _run_loop(self) -> None:
        """
        Starts and awaits the run loops of all READY managed services.

        This method assumes that `_connect` has completed successfully and that
        all managed services are already in the READY state. Any failure during
        execution is propagated to ensure the manager does not silently enter
        an inconsistent RUNNING state.
        """
        if not self.managed_services:
            return

        run_tasks = [
            asyncio.create_task(service._run_loop())
            for service in self.managed_services
            if hasattr(service, "_run_loop") and service.is_ready()
        ]

        if not run_tasks:
            self.logger.warning(
                f"No READY service run loops to start for '{self.service_name}'."
            )
            return

        self.logger.info(
            f"Starting main loop for {len(run_tasks)} managed service(s)..."
        )

        await asyncio.gather(*run_tasks)

    async def _close(self) -> None:
        """
        Stops all managed client services.

        Shutdown is executed in a best-effort manner. All managed services are
        given a chance to stop, and any errors raised during shutdown are logged
        without aborting the overall close sequence.
        """
        self.logger.info(
            f"Stopping all {len(self.managed_services)} connections for '{self.service_name}'..."
        )

        for client in reversed(self.managed_services):
            try:
                await client.stop()
            except Exception:
                self.logger.exception(
                    f"Error while stopping client '{client.service_name}'."
                )

        self._managed_clients.clear()
        self.managed_services.clear()

        self.logger.success(
            f"All connections for '{self.service_name}' have been closed."
        )

    def get_client(self, name: Optional[str] = None) -> ClientProtocolT:
        """
        Fetches a connected client instance by its name.

        If a name is not provided, it returns the default instance.
        """
        if not self.is_ready():
            raise RuntimeError(
                f"{self.service_name} is not ready. Has the application started?"
            )

        connection_name = name or self.settings.default_connection_name

        if not connection_name:
            raise ValueError(
                "Connection name not specified and no default is configured."
            )

        try:
            return self._managed_clients[connection_name]
        except KeyError:
            self.logger.error(
                f"Available clients for '{self.service_name}': {list(self._managed_clients.keys())}"
            )
            raise KeyError(
                f"Client with name '{connection_name}' not found or not configured."
            )

    def health(self) -> Dict[str, Any]:
        """
        Returns an aggregated health view of all managed services.

        The manager is considered healthy only if all managed services
        are healthy. This method is intended for observability and
        health-check endpoints.
        """
        services_health = {
            name: service.health() for name, service in self._managed_clients.items()
        }

        all_ready = all(h["ready"] for h in services_health.values())
        any_failed = any(h["state"] == "FAILED" for h in services_health.values())

        return {
            "service_name": self.service_name,
            "managed_services": services_health,
            "ready": all_ready,
            "failed": any_failed,
            "count": len(services_health),
        }
