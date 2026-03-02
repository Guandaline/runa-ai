# File: src/nala/athomic/lifecycle/initializers.py

from typing import Callable, Coroutine, List

from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class DomainInitializerRegistry:
    """A singleton registry for domain-specific initialization functions.

    This class allows the main application (the "domain") to register its own
    asynchronous setup functions. The LifecycleManager can then retrieve and
    execute these functions during the application startup sequence, decoupling
    the framework's startup from the application's specific logic.

    Attributes:
        _instance: The singleton instance of the class.
        _initializers: A list of registered asynchronous functions.
    """

    _instance = None
    _initializers: List[Callable[[], Coroutine]] = []

    def __new__(cls) -> "DomainInitializerRegistry":
        """Ensures that only one instance of the registry is created (Singleton pattern).

        Returns:
            DomainInitializerRegistry: The singleton instance of the registry.
        """
        if cls._instance is None:
            cls._instance = super(DomainInitializerRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, func: Callable[[], Coroutine]) -> None:
        """Registers an asynchronous initialization function.

        Args:
            func (Callable[[], Coroutine]): The asynchronous function to be
                registered. It should contain domain-specific setup logic
                to be executed during application startup.
        """
        logger.debug(f"Registering domain initializer: {func.__name__}")
        self._initializers.append(func)

    def get_initializers(self) -> List[Callable[[], Coroutine]]:
        """Returns all registered initialization functions.

        Returns:
            List[Callable[[], Coroutine]]: A list of all registered async
            initializer functions.
        """
        return self._initializers


# Singleton instance
domain_initializer_registry = DomainInitializerRegistry()
