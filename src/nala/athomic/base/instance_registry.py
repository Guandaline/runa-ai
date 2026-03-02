import inspect
from typing import Dict, Generic, Optional, Type, TypeVar

from nala.athomic.observability import get_logger

T = TypeVar("T")


class BaseInstanceRegistry(Generic[T]):
    """
    Registry responsible for managing live object instances.

    This registry enforces deterministic lookup semantics through
    consistent key normalization and optional protocol validation.
    """

    def __init__(self, protocol: Optional[Type[T]] = None) -> None:
        self._registry: Dict[str, T] = {}
        self._protocol = protocol
        self._logger = get_logger(self.__class__.__name__)

    def _normalize_key(self, name: str) -> str:
        """
        Normalizes registry keys to ensure consistent lookup behavior.
        """
        return name.lower()

    def _validate_protocol(self, instance: T) -> None:
        """
        Validates that the instance conforms to the configured protocol.
        """
        if not self._protocol:
            return

        if inspect.isclass(self._protocol) and hasattr(self._protocol, "_is_protocol"):
            if getattr(self._protocol, "_is_runtime_protocol", False):
                if not isinstance(instance, self._protocol):
                    raise TypeError(
                        f"Instance '{type(instance).__name__}' does not implement "
                        f"runtime protocol '{self._protocol.__name__}'."
                    )
            else:
                if self._protocol not in inspect.getmro(type(instance)):
                    raise TypeError(
                        f"Instance '{type(instance).__name__}' must explicitly inherit "
                        f"from protocol '{self._protocol.__name__}'."
                    )
        else:
            if not isinstance(instance, self._protocol):
                raise TypeError(
                    f"Instance '{type(instance).__name__}' does not match "
                    f"expected type '{self._protocol.__name__}'."
                )

    def register(self, name: str, item_instance: T) -> None:
        """
        Registers an instance under a normalized name.
        """
        key = self._normalize_key(name)
        self._validate_protocol(item_instance)
        instance_name = type(item_instance).__name__

        if key in self._registry:
            self._logger.warning(
                f"Overwriting existing instance '{key}' with {instance_name}."
            )

        self._registry[key] = item_instance

        self._logger.info(f"Registered instance '{key}' {instance_name}.")

    def get(self, name: str) -> T:
        """
        Retrieves a registered instance by name.

        Raises:
            ValueError: If the instance is not registered.
        """
        key = self._normalize_key(name)

        if key not in self._registry:
            raise ValueError(
                f"Instance '{key}/{name}' is not registered in {self.__class__.__name__}."
            )

        return self._registry.get(key)

    def all(self) -> Dict[str, T]:
        """
        Returns a shallow copy of all registered instances.
        """
        return self._registry.copy()

    async def clear(self) -> None:
        """
        Stops all managed instances and clears the registry.
        """
        for instance in self._registry.values():
            if hasattr(instance, "stop") and callable(instance.stop):
                await instance.stop()
            elif hasattr(instance, "close") and callable(instance.close):
                await instance.close()

        self._logger.info("Clearing registry and stopping all managed instances.")
        self._registry.clear()

    def remove(self, name: str) -> T:
        """
        Removes a registered instance.

        Raises:
            ValueError: If the instance is not registered.
        """
        key = self._normalize_key(name)

        if key not in self._registry:
            raise ValueError(
                f"Instance '{name}' is not registered in {self.__class__.__name__}."
            )

        instance = self._registry.pop(key)

        self._logger.info(
            "Removed instance '%s' (%s).",
            key,
            type(instance).__name__,
        )

        return instance
