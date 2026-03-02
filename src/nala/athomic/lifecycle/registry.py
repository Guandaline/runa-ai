# File: src/nala/athomic/lifecycle/registry.py

from typing import List, Optional, Tuple

from ..base.instance_registry import BaseInstanceRegistry
from ..services import BaseServiceProtocol


class LifecycleRegistry(BaseInstanceRegistry[BaseServiceProtocol]):
    """A specialized registry for services with a manageable lifecycle.

    This class extends BaseInstanceRegistry by adding a priority system to
    control the startup and shutdown order of services. Services with a lower
    priority number are started first and stopped last, which is essential for
    managing dependencies (e.g., ensuring a database service is available
    before a repository service that uses it).

    Attributes:
        _registry_with_priority (List[Tuple[int, str, BaseServiceProtocol]]): An internal
            list that stores services along with their priority, sorted on insertion.
    """

    def __init__(self, protocol: BaseServiceProtocol):
        """Initializes the LifecycleRegistry.

        Args:
            protocol: The protocol that all registered items must conform to.
        """
        super().__init__(protocol)
        self._registry_with_priority: List[Tuple[int, str, BaseServiceProtocol]] = []

    def register(
        self,
        name: str,
        item_instance: BaseServiceProtocol,
        priority: Optional[int] = 100,
    ):
        """Registers a service instance with a specific priority.

        Args:
            name (str): The unique string name for the service instance.
            item_instance (BaseServiceProtocol): The service object to register.
            priority (Optional[int]): The startup priority. Lower numbers are
                started earlier and stopped later. Defaults to 100.
        """
        super().register(name, item_instance)
        # Prevents duplicates in the priority list
        if not any(s[1] == name for s in self._registry_with_priority):
            self._registry_with_priority.append((priority, name, item_instance))
            self._registry_with_priority.sort(key=lambda x: x[0])

    def get_services_by_priority(self) -> List[BaseServiceProtocol]:
        """Returns all registered services, sorted by startup priority.

        Returns:
            List[BaseServiceProtocol]: A list of service instances ordered from
            lowest to highest priority, ready for startup.
        """
        return [service for priority, name, service in self._registry_with_priority]

    async def clear(self) -> None:
        """Stops all services and completely clears the registry.

        This method overrides the parent `clear` to also purge the internal
        priority list, ensuring a complete reset for testing or re-initialization.
        """
        await super().clear()
        self._registry_with_priority.clear()


lifecycle_registry = LifecycleRegistry(protocol=BaseServiceProtocol)


def get_lifecycle_registry() -> LifecycleRegistry:
    """Returns the singleton instance of the lifecycle registry.

    This function serves as a convenient, global access point to the
    `lifecycle_registry` instance used throughout the application.

    Returns:
        LifecycleRegistry: The singleton registry instance.
    """
    return lifecycle_registry
