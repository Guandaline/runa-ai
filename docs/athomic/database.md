# Database Connection Management

## Overview

The `athomic.database` module provides a centralized, lifecycle-managed system for all data store connections within the application. Its primary component, the `ConnectionManager`, acts as a registry and orchestrator for all configured data stores, including Document Databases (like MongoDB) and Key-Value Stores (like Redis).

This system is crucial for building robust applications as it ensures that:

-   All database connections are established and checked for readiness during application startup.
-   Dependencies are respected, so services that require a database connection only start after the connection is ready.
-   All connections are gracefully closed during application shutdown.

---

## Core Components

### `ConnectionManager`

The `ConnectionManager` is the heart of the database module. It is a `BaseService` whose lifecycle is managed by the main `LifecycleManager`. Its responsibilities are:

-   **Reading Configuration**: It inspects the `[database]` section of your settings file to discover all configured connections.
-   **Creating Providers**: For each configured connection, it uses a dedicated factory (e.g., `DocumentsDatabaseFactory`, `KVStoreFactory`) to instantiate the correct provider client.
-   **Managing Lifecycle**: It concurrently starts (`connect`) and checks the readiness (`wait_ready`) of all provider instances during startup, and gracefully closes them during shutdown.
-   **Acting as a Registry**: It provides getter methods (`get_document_db`, `get_kv_store`) for other services to retrieve active and ready-to-use database clients.

### `ConnectionManagerFactory`

This is a singleton factory responsible for creating the single instance of the `ConnectionManager`. Any component in the application that needs access to a database connection should use this factory to get the `ConnectionManager`.

---

## How It Works

### Startup Sequence

1.  During application startup, the main `LifecycleManager` starts the `ConnectionManager` service.
2.  The `ConnectionManager` reads the settings and identifies all connections defined under `[database.documents]` and `[database.kvstore]`.
3.  It then concurrently calls the `connect()` and `wait_ready()` methods on each of these connection providers.
4.  The `ConnectionManager` itself becomes "ready" only after all its managed connections are successfully established.

### Retrieving a Connection

A service that needs to interact with a database follows these steps:

1.  Get the singleton `ConnectionManager` instance from the `ConnectionManagerFactory`.
2.  Call the appropriate getter method with the name of the desired connection, for example: `connection_manager.get_document_db("default_mongo")`.

This call will return a client instance that is guaranteed to be connected and ready to use.

---

## Configuration

You can define multiple connections for both document databases and key-value stores in your `settings.toml` file. This is useful for connecting to different databases for different purposes (e.g., one for application data, another for caching).

```toml
[default.database]
# Define the names of the default connections to be used by other modules.
default_document_connection = "default_mongo"
default_kvstore_connection = "default_redis"

# A dictionary of all available document database connections.
[default.database.documents]
  [default.database.documents.default_mongo]
  enabled = true
  backend = "mongo"
    [default.database.documents.default_mongo.provider]
    url = "mongodb://user:pass@localhost:27017" # pragma: allowlist secret
    database_name = "main_db"

# A dictionary of all available key-value store connections.
[default.database.kvstore]
  [default.database.kvstore.default_redis]
  enabled = true
  namespace = "cache"
    [default.database.kvstore.default_redis.provider]
    backend = "redis"
    uri = "redis://localhost:6379/0"
  
  [default.database.kvstore.another_redis]
  enabled = true
  namespace = "sessions"
    [default.database.kvstore.another_redis.provider]
    backend = "redis"
    uri = "redis://localhost:6379/1"
```

---

## API Reference

::: nala.athomic.database.manager.ConnectionManager

::: nala.athomic.database.factory.ConnectionManagerFactory

::: nala.athomic.database.protocol.DatabaseClientProtocol