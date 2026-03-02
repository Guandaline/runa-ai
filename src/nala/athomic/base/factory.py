# src/nala/athomic/base/factory.py
from typing import Any, Generic, Protocol, TypeVar

# T is the type variable for the "Product" created by the factory (e.g., SchemaHandlerProtocol)
T = TypeVar("T")
# C is the type variable for the "Configuration" object the factory uses (e.g., MessagingSerializerConfig)
C = TypeVar("C")


class FactoryProtocol(Protocol, Generic[T, C]):
    """Defines the abstract contract for all factory implementations within the framework.

    This protocol enforces a standard interface for creating objects ('products')
    from a configuration object, ensuring architectural consistency across all
    Athomic modules and adherence to the Open/Closed Principle (OCP).
    """

    @classmethod
    def create(cls, settings: C, **kwargs: Any) -> T:
        """Abstract method to create an instance of the product type 'T'.

        Subclasses must implement this method to provide the concrete logic
        for object creation based on the provided configuration.

        Args:
            settings: The configuration object that guides the creation process.
            **kwargs: Additional optional parameters that might be needed by the factory
                      (e.g., dependencies for dependency injection).

        Returns:
            An instance of the product type T.
        """
        raise NotImplementedError
