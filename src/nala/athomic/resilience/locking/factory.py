# src/nala/athomic/resilience/locking/factory.py
from typing import Optional

from nala.athomic.config import LockingSettings, get_settings
from nala.athomic.database.kvstore.factory import KVStoreFactory
from nala.athomic.observability import get_logger

from .protocol import LockingProtocol
from .registry import locking_registry

logger = get_logger(__name__)


class LockingFactory:
    """
    Factory to create or obtain the singleton instance of a locking provider.
    Allows injection of settings for tests or specific scenarios.
    """

    _instance: Optional[LockingProtocol] = None

    @classmethod
    def create(
        cls, settings: Optional[LockingSettings] = None, *, ignore_cache: bool = False
    ) -> LockingProtocol:
        """
        Creates or returns an instance of a locking provider.

        - If 'settings' is not provided, returns the global singleton instance.
        - If 'settings' is provided, creates a NEW instance based on those
          settings, ignoring the cache (ideal for tests).

        Args:
            settings: Locking settings to use. If None, uses the global ones.
            ignore_cache: If True, forces creation of a new global instance.

        Returns:
            An instance implementing the LockingProtocol.
        """
        # If 'settings' was injected, always create a new instance.
        create_new_instance = settings is not None or ignore_cache

        if not create_new_instance and cls._instance:
            logger.debug("Returning cached singleton instance of the locking provider.")
            return cls._instance

        # If there is no cached instance or creation was forced, determine which settings to use.
        effective_settings = settings
        if effective_settings is None:
            logger.debug("Locking settings not injected, using global settings.")
            try:
                effective_settings = get_settings().resilience.locking
            except AttributeError:
                raise RuntimeError(
                    "The configuration section 'resilience.locking' is missing."
                )

        if not effective_settings or not effective_settings.enabled:
            logger.warning(
                "Locking is disabled. Using 'in_memory' provider as a safe fallback."
            )
            provider_cls = locking_registry.get(name="in_memory")
            return provider_cls()

        # Pydantic has already validated and loaded the correct provider configuration
        provider_config = effective_settings.provider
        backend_name = provider_config.backend

        logger.info(f"Creating locking provider for backend: '{backend_name}'")
        provider_cls = locking_registry.get(backend_name)

        if not provider_cls:
            raise ValueError(
                f"Lock provider not registered for backend: '{backend_name}'"
            )

        # Instantiation logic based on backend
        try:
            if backend_name == "redis":
                kv_client = KVStoreFactory.create(settings=provider_config.kvstore)
                instance = provider_cls(kv_store_client=kv_client)
            else:  # 'in_memory' or other future simple providers
                instance = provider_cls()

        except Exception as e:
            logger.exception(
                f"Failed to instantiate lock provider for backend '{backend_name}'"
            )
            raise RuntimeError(f"Could not create lock provider: {e}") from e

        # Cache only if this is the global instance (no injected settings)
        if not settings:
            cls._instance = instance

        return instance

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the cached singleton instance. Useful for tests."""
        cls._instance = None
        logger.info("LockingFactory cache cleared.")
