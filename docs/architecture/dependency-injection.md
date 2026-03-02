# Dependency Injection & Service Location

## Overview

The `athomic` project manages dependencies and object lifecycles without relying on an external dependency injection framework. Instead, it employs a robust and clear approach using a combination of two classic design patterns:

1.  **The Facade Pattern**: The `Athomic` class acts as a central service locator, providing a single, unified entry point to all core framework services.
2.  **The Factory Pattern**: Dedicated `Factory` classes are responsible for creating and managing singleton instances of specific components, handling their unique dependencies internally.

This approach promotes loose coupling, simplifies testing through easy mocking, and makes the flow of dependency resolution explicit and easy to follow.

---

## The `Athomic` Façade

The main entry point to the entire framework is the `nala.athomic.facade.Athomic` class. During application startup, this class is instantiated once. Its constructor (`__init__`) is responsible for wiring together the primary, high-level services.

```python
# From: nala.athomic.facade.py
class Athomic:
    def __init__(self, ...):
        # ...
        self.settings = settings or get_settings()
        self.secrets_manager = SecretsManager(self.settings)
        self.lifecycle_manager = LifecycleManager(...)
        self.tracer = get_tracer(__name__)
        self.plugin_manager: PluginManager = PluginManager()
        # ...
```

The `nala.athomic.provider` module then makes this single `Athomic` instance globally accessible via the `get_athomic_instance()` function, allowing any part of the application to access core services like the `LifecycleManager` or `PluginManager` when needed.

---

## The Factory Pattern

For most components within the Athomic Layer, a dedicated factory is responsible for its creation. This pattern provides several key advantages:

-   **Centralized Creation Logic**: The logic for creating a complex object (e.g., a `ConnectionManager` that needs `DatabaseSettings`) is encapsulated in one place.
-   **Singleton Management**: Factories typically manage a singleton instance of the object they create, ensuring resources like connection pools are shared efficiently.
-   **Simplified Dependency Injection**: Components that need a dependency can simply call the factory's `create()` method without needing to know how to construct it.
-   **Testability**: Factories usually include a `.clear()` method, which is crucial for resetting state between tests and ensuring test isolation.

### Example Flow

A great example is the `MongoOutboxRepository`. It needs a database connection to work. Here is how its dependencies are resolved:

1.  The application needs an `OutboxStorageProtocol` instance.
2.  It calls `OutboxStorageFactory.create()`.
3.  The `OutboxStorageFactory` knows it needs a database connection. It calls `connection_manager_factory.create()`.
4.  The `ConnectionManagerFactory` creates the singleton `ConnectionManager`.
5.  The `OutboxStorageFactory` then asks the `ConnectionManager` for the specific database connection (`get_document_db(...)`).
6.  Finally, it injects the database connection into a new `MongoOutboxRepository` instance and returns it.

This chain of factory calls ensures that dependencies are resolved correctly and only when needed.

---

## API Reference

### Core Façade and Provider

::: nala.athomic.facade.Athomic

::: nala.athomic.provider

### Example Factories

::: nala.athomic.database.factory.ConnectionManagerFactory

::: nala.athomic.serializer.factory.SerializerFactory