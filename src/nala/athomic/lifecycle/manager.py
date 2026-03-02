# File: src/nala/athomic/lifecycle/manager.py

import asyncio
from typing import Callable, Optional

from nala.athomic.config.schemas.app_settings import AppSettings
from nala.athomic.config.settings import get_settings
from nala.athomic.observability import get_logger
from nala.athomic.services.base import BaseService

from .registry import lifecycle_registry

logger = get_logger(__name__)


class LifecycleManager:
    """Orchestrates the application lifecycle for all Athomic and Domain services.

    This class is the central coordinator for service startup and shutdown. It ensures
    that dependencies are respected by starting and stopping services based on a
    priority system. It first registers all framework-level infrastructure
    services and then allows the application to register its own domain-specific
    services before managing their execution order.

    Attributes:
        settings (AppSettings): The application's configuration settings.
    """

    def __init__(
        self,
        domain_initializers_register: Optional[Callable[[], None]] = None,
        settings: Optional[AppSettings] = None,
    ):
        """Initializes the LifecycleManager.

        This constructor registers all of Athomic's internal infrastructure services
        and then executes the provided domain initializer callback to allow the
        application to register its own services into the lifecycle registry.

        Args:
            domain_initializers_register (Optional[Callable[[], None]]): An optional
                function that, when called, registers all domain-specific
                initializers and services.
            settings (Optional[AppSettings]): The application settings instance. If not
                provided, global settings will be used.
        """
        self.settings: AppSettings = settings or get_settings()
        logger.debug(f"Initializing LifecycleManager with settings: {self.settings}")

        if callable(domain_initializers_register):
            logger.info("Registering application domain initializers...")
            try:
                domain_initializers_register()
            except Exception as e:
                logger.critical(f"Error while registering domain initializers: {e}")
                raise

    async def startup(self) -> None:
        """Executes the startup sequence for all registered services.

        It retrieves all services from the registry, sorted by their priority,
        and starts each one sequentially. A timeout is applied to each service's
        startup to prevent the application from hanging.
        """
        logger.info("Application Startup Sequence")

        all_services = lifecycle_registry.get_services_by_priority()

        logger.info("Starting core infrastructure services...")

        service: Optional[BaseService] = None

        for service in all_services:
            logger.debug(f"Starting service: {service.service_name}")

            async with asyncio.timeout(self.settings.timeout):
                await service.start()

        logger.info("Core infrastructure started.")

    async def shutdown(self) -> None:
        """Executes the graceful shutdown sequence for all registered services.

        It retrieves services and stops them in reverse priority order to correctly
        handle dependencies during shutdown. A timeout is applied to each `stop`
        operation, and any errors are logged without halting the shutdown of
        other services.
        """
        logger.info("Application Shutdown Sequence")

        logger.info(
            "Stopping core infrastructure services in reverse priority order..."
        )

        # Get the same priority-sorted list used for startup and reverse it
        services_to_shutdown = reversed(lifecycle_registry.get_services_by_priority())

        service: Optional[BaseService] = None

        for service in services_to_shutdown:
            # The timeout is now applied per service shutdown, which is more robust
            try:
                logger.debug(f"Stopping service: {service.service_name}")
                async with asyncio.timeout(self.settings.timeout):
                    await service.stop()
            except TimeoutError:
                logger.error(
                    f"Timeout occurred while stopping service: {service.service_name}"
                )
            except Exception:
                logger.exception(
                    f"An error occurred while stopping service: {service.service_name}"
                )

        logger.success("Application Shutdown Complete")
