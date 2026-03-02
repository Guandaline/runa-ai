# src/nala/athomic/ai/agents/persistence/factory.py
from typing import Optional

from nala.athomic.ai.agents.persistence.protocol import CheckpointProtocol
from nala.athomic.ai.agents.persistence.registry import checkpoint_registry
from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.agents.persistence_settings import (
    AgentPersistenceSettings,
)
from nala.athomic.database.factory import connection_manager_factory
from nala.athomic.observability import get_logger
from nala.athomic.services.exceptions import ProviderInitializationError

logger = get_logger(__name__)


class CheckpointFactory:
    """
    Factory for creating Agent Persistence Providers.

    Acts as the Composition Root for the persistence module. It resolves
    infrastructure dependencies (Database Connection, Serializer) dynamically
    based on the configured strategy and instantiates the provider.
    """

    @staticmethod
    def create(
        settings: Optional[AgentPersistenceSettings] = None,
    ) -> CheckpointProtocol:
        """
        Creates a fully configured Checkpoint Provider instance.

        Args:
            settings: Optional configuration override. If None, loads from global settings.

        Returns:
            CheckpointProtocol: The initialized provider instance.
        """
        if settings is None:
            settings = get_settings().ai.agents.persistence

        if not settings.enabled:
            logger.info("Agent State Persistence is disabled via configuration.")

        strategy = settings.strategy.lower()

        # 1. Get the Provider Class from the Registry
        provider_cls = checkpoint_registry.get(strategy)
        if not provider_cls:
            raise ValueError(
                f"Checkpoint Strategy '{strategy}' is not registered in CheckpointRegistry. "
                f"Available: {list(checkpoint_registry.get_all().keys())}"
            )

        logger.debug(
            f"Creating Checkpoint Provider. Strategy='{strategy}', "
            f"Class='{provider_cls.__name__}', Connection='{settings.connection_name}'"
        )

        # 2. Resolve Infrastructure Dependencies
        db_manager = connection_manager_factory.create()

        # 3. Resolve Connection Genericly using the new Dispatch Method
        # The strategy name (e.g., 'kv_store', 'document') maps directly to the
        # connection type expected by db_manager.get()
        try:
            connection = db_manager.get(
                connection_type=strategy, name=settings.connection_name
            )
        except (ValueError, RuntimeError, KeyError) as e:
            raise ProviderInitializationError(
                service_name="checkpoint_factory",
                message=f"Failed to resolve connection '{settings.connection_name}' for type '{strategy}': {e}",
            ) from e

        # 4. Instantiate Provider
        # We perform a specific check to inject the correct arguments based on the strategy.
        # This keeps the providers clean and strongly typed.
        if strategy == "kv_store":
            return provider_cls(
                kv_store=connection,
                namespace=settings.namespace,
                ttl_seconds=settings.ttl_seconds,
            )
        elif strategy == "document":
            return provider_cls(
                db_client=connection,
                collection_name=settings.namespace,  # Namespace acts as collection name
                ttl_seconds=settings.ttl_seconds,
            )
        else:
            raise NotImplementedError(
                f"Factory instantiation logic for strategy '{strategy}' is not implemented."
            )
