#
# src/nala/athomic/facade.py
#
from typing import Callable, Optional

from nala.athomic import observability

from .config import get_settings
from .config.schemas.app_settings import AppSettings
from .lifecycle import register_athomic_infra_services
from .lifecycle.manager import LifecycleManager
from .observability import get_logger
from .observability.tracing import SpanKind, StatusCode, get_tracer

logger = get_logger(__name__)


class Athomic:
    """A Facade that provides a single, simple entry point to all of Athomic's services.

    This class acts as the main interaction point for an application utilizing
    the Athomic framework. It manages the initialization, dependency injection,
    and lifecycle of all infrastructure components, such as secrets management
    and background services.

    Attributes:
        settings (AppSettings): The validated application settings.
        secrets_manager (SecretsManager): The manager responsible for resolving secrets.
        lifecycle_manager (LifecycleManager): The orchestrator for the service lifecycle.
        plugin_manager (PluginManager): The manager for the plugin system.
        tracer (Tracer): The OpenTelemetry Tracer instance for this component.
        observability: A namespace for observability components like loggers.
    """

    def __init__(
        self,
        domain_initializers_registrar: Optional[Callable[[], None]] = None,
        settings: Optional[AppSettings] = None,
    ):
        """Initializes the Athomic layer.

        Args:
            domain_initializers_registrar (Optional[Callable[[], None]]): A function from
                the application layer (e.g., API) that registers all business
                domain-specific initializers.
            settings (Optional[AppSettings]): An instance of application settings.
                If not provided, it will be loaded globally. Ideal for
                dependency injection in tests.
        """
        logger.info("Initializing Athomic Facade (Composition Root)...")
        self.settings = settings or get_settings()

        # --- Composition Root: Create and inject dependencies ---

        # 1. Register all internal framework services into the lifecycle registry.
        # This will create the singleton ConnectionManager instance via its factory.
        register_athomic_infra_services(settings=self.settings)

        self.lifecycle_manager = LifecycleManager(
            settings=self.settings,
            domain_initializers_register=domain_initializers_registrar,
        )
        # --- End Composition Root ---

        self.tracer = get_tracer(__name__)
        self.observability = observability

    async def startup(self) -> None:
        """Runs the complete, ordered startup sequence for the application's infrastructure.

        This method orchestrates the startup of services in the correct dependency order:
        1. Resolves all secret references within the configuration.
        2. Discovers and loads all available plugins.
        3. Calls the 'on_athomic_startup' hook, allowing plugins to initialize.
        4. Starts all registered services (e.g., database, messaging).

        Raises:
            RuntimeError: If any critical step in the startup sequence fails.
        """
        with self.tracer.start_as_current_span(
            "AthomicFacade.startup", kind=SpanKind.INTERNAL
        ) as span:
            try:
                logger.info("--- Athomic Startup Sequence Initiated ---")
                # 4. Start all registered services (which now have resolved settings).
                await self.lifecycle_manager.startup()
                logger.success("--- Athomic Startup Sequence Complete ---")
                span.set_status(StatusCode.OK, "Athomic startup successful")
            except Exception as e:
                logger.exception("Athomic startup sequence failed critically.")
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=f"Startup failed: {e}")
                raise RuntimeError("Athomic startup failed") from e

    async def shutdown(self) -> None:
        """Runs the graceful shutdown sequence for all services."""
        with self.tracer.start_as_current_span(
            "AthomicFacade.shutdown", kind=SpanKind.INTERNAL
        ) as span:
            try:
                logger.info("--- Athomic Shutdown Sequence Initiated ---")
                await self.lifecycle_manager.shutdown()
                logger.success("--- Athomic Shutdown Sequence Complete ---")
                span.set_status(StatusCode.OK, "Athomic shutdown successful")
            except Exception as e:
                logger.exception("Athomic shutdown sequence encountered an error.")
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=f"Shutdown failed: {e}")
                raise
