# src/nala/athomic/database/kvstore/factory.py

from nala.athomic.base import FactoryProtocol
from nala.athomic.config.schemas.database.kvstore import (
    KVStoreSettings,
)
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.observability.log import get_logger

from .base import BaseKVStore
from .registry import kv_store_registry
from .wrappers.registry import kv_store_wrapper_registry

logger = get_logger(__name__)


class KVStoreFactory(FactoryProtocol):
    @classmethod
    def create(cls, settings: KVStoreSettings) -> BaseKVStore:
        """
        Factory that creates a KVStore client based on the provided KVStoreSettings.
        Applies wrappers as defined INSIDE the kv_config.
        """

        logger.debug(f"KVStore settings: {settings}")

        backend_name = settings.provider.backend

        logger.debug(
            f"Creating KVStore client instance based on provided KVStoreSettings (Backend: {backend_name})"
        )

        provider_cls = kv_store_registry.get(name=backend_name)

        if not provider_cls:
            logger.error(f"KVStore provider '{backend_name}' not found in registry")
            raise ValueError(f"KVStore provider '{backend_name}' is not registered")

        if not issubclass(provider_cls, KVStoreProtocol):
            logger.error(
                f"KVStore provider '{backend_name}' is not a valid KVStoreProtocol subclass"
            )
            raise TypeError(
                f"KVStore provider '{backend_name}' must be a subclass of KVStoreProtocol"
            )

        current_client = provider_cls(settings=settings)

        for wrapper_settings in settings.wrappers:
            if not getattr(wrapper_settings, "enabled", False):
                continue

            wrapper_name = wrapper_settings.name
            logger.debug(f"Applying KVStore wrapper: '{wrapper_name}'")

            wrapper_cls = kv_store_wrapper_registry.get(wrapper_name)

            if not wrapper_cls:
                logger.warning(
                    f"Wrapper '{wrapper_name}' not found in registry. Skipping."
                )
                continue

            current_client = wrapper_cls(
                client=current_client,
                settings=settings,
                wrapper_settings=wrapper_settings,
            )

        logger.success(
            f"KVStore successfully created with client chain: {type(current_client).__name__}"
        )

        return current_client
