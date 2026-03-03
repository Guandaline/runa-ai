# src/nala/athomic/lifecycle/register_services.py
from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.app_settings import AppSettings
from nala.athomic.database.factory import connection_manager_factory
from nala.athomic.ai.llm import llm_manager
from nala.athomic.observability import get_logger
from nala.athomic.observability.metrics import MetricSchedulerFactory

from .registry import lifecycle_registry

logger = get_logger(__name__)


def _register_level_10_services(settings: AppSettings) -> None:
    connection_manager = connection_manager_factory.create(settings=settings.database)

    lifecycle_registry.register(
        connection_manager.service_name, connection_manager, priority=10
    )


def _register_level_20_services() -> None:
    
    lifecycle_registry.register(llm_manager.service_name, llm_manager, priority=20)


def _register_level_50_services(settings: AppSettings) -> None:
    if settings.observability and settings.observability.enabled:
        logger.debug("Registering ObservabilityService...")
        observability_service = MetricSchedulerFactory.create()
        lifecycle_registry.register(
            observability_service.service_name, observability_service, priority=50
        )


def _register_level_100_services(settings: AppSettings) -> None:
    pass  # Placeholder


def register_athomic_infra_services(settings: Optional[AppSettings] = None) -> None:
    """
    Instantiates and registers all Athomic infrastructure services,
    handling the dependency injection between them with priority.
    """
    logger.info("Registering Athomic's core infrastructure services...")
    settings: AppSettings = settings or get_settings()

    # --- Level 0: Fundamental Dependencies (not lifecycle services) ---

    # --- Level 10: Basic Network Connections (Vault, DBs, Consul) ---
    _register_level_10_services(settings)

    # --- Level 20: Infrastructure Clients depending on base connections ---
    _register_level_20_services()

    # --- Level 50: Infrastructure Business Logic Services ---
    _register_level_50_services(settings)

    # --- Level 100: Application Services (depend on infra services) ---
    _register_level_100_services(settings)

    logger.info("Core infrastructure services registered.")
