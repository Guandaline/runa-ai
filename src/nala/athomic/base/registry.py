import inspect
from abc import ABC
from typing import Callable, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel

from nala.athomic.observability import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BaseRegistry(ABC, Generic[T]):
    """
    A base class for creating provider registries with decorator support.

    This registry manages class-based providers bound to an explicit protocol.
    Contract validation is performed at registration time to guarantee
    correctness and fail fast during application bootstrap.
    """

    def __init__(self, protocol: Type[T]):
        """
        Initializes a new registry instance bound to a specific protocol.
        """
        self._registry: Dict[str, Type[T]] = {}
        self._protocol = protocol
        logger.debug(
            f"Instance of {self.__class__.__name__} created for protocol {protocol.__name__}."
        )
        self.register_defaults()

    def exists(self, name: str) -> bool:
        """
        Checks if a class is registered under the given name.
        """
        return name.lower() in self._registry

    def register(
        self,
        name: str,
        item_class: Optional[Type[T]] = None,
        overwrite: Optional[bool] = False,
    ) -> Optional[Callable[[Type[T]], Type[T]]]:
        """
        Registers a class in the registry.

        This method supports both direct invocation and decorator usage.
        """
        if item_class is None:

            def decorator(cls_to_register: Type[T]) -> Type[T]:
                self._register_item(name, cls_to_register, overwrite)
                return cls_to_register

            return decorator

        self._register_item(name, item_class, overwrite)
        return None

    def _register_item(
        self, name: str, item_class: Type[T], overwrite: Optional[bool] = False
    ) -> None:
        """
        Validates and registers a class under a normalized name.

        Validation rules:
        - ABCs and concrete base classes are validated via issubclass
        - runtime-checkable Protocols are validated via issubclass
        - non-runtime Protocols require explicit inheritance
        """
        if not inspect.isclass(item_class):
            raise TypeError(
                f"Only classes can be registered in {self.__class__.__name__}."
            )

        if self._protocol:
            if self._is_runtime_validatable_protocol(self._protocol):
                if not issubclass(item_class, self._protocol):
                    raise TypeError(
                        f"Class '{item_class.__name__}' does not implement "
                        f"the required protocol '{self._protocol.__name__}'."
                    )
            else:
                if self._protocol not in inspect.getmro(item_class):
                    raise TypeError(
                        f"Class '{item_class.__name__}' must explicitly inherit "
                        f"from protocol '{self._protocol.__name__}'."
                    )

        normalized_name = name.lower()

        if self.exists(name) and not overwrite:
            raise ValueError(
                f"Item '{normalized_name}' is already registered in "
                f"{self.__class__.__name__}."
            )

        logger.info(
            f"Registered '{normalized_name}' -> {item_class.__name__} "
            f"in {self.__class__.__name__}."
        )

        self._registry[normalized_name] = item_class

    @staticmethod
    def _is_runtime_validatable_protocol(protocol: Type) -> bool:
        """
        Determines whether a protocol can be safely validated using issubclass.
        """
        return (
            inspect.isclass(protocol)
            and hasattr(protocol, "_is_protocol")
            and getattr(protocol, "_is_runtime_protocol", False)
        )

    def get(self, name: str) -> Type[T]:
        """
        Retrieves a registered class by its name.
        """
        key = name.lower()
        if key not in self._registry:
            raise ValueError(
                f"Item '{name}' is not registered in {self.__class__.__name__}."
            )
        return self._registry[key]

    def create(self, name: str, settings: Optional[BaseModel] = None, **kwargs) -> T:
        """
        Instantiates a registered class using keyword arguments.
        """
        cls = self.get(name)

        try:
            if settings is not None:
                return cls(settings=settings, **kwargs)

            return cls(**kwargs)

        except TypeError as exc:
            raise TypeError(
                f"Failed to instantiate '{cls.__name__}' from "
                f"{self.__class__.__name__}: {exc}"
            ) from exc

    def clear(self) -> None:
        """
        Clears all registered items.
        """
        self._registry.clear()

    def get_all(self) -> Dict[str, Type[T]]:
        """
        Returns all registered items.
        """
        return self._registry.copy()

    def register_defaults(self) -> None:
        """
        Registers default items for the registry.
        """
        ...
