# Configuration Schemas

## Overview

The `config/schemas` directory is the heart of the Athomic Layer's type-safe configuration system. It contains a collection of Pydantic models that precisely define the structure, data types, default values, and validation rules for every setting in the application.

This approach provides several key benefits:
-   **Type Safety**: Eliminates configuration errors at startup by validating the entire settings structure.
-   **Auto-Completion**: Developers get full auto-completion and static analysis for configuration objects in their IDE.
-   **Clear Structure**: The directory structure of the schemas directly mirrors the structure of the `settings.toml` file, making the configuration intuitive to navigate.

The root of this system is the `AppSettings` model, which composes all other schema models into a single, unified configuration object.

---

## Schema Module Structure

Below is a list of the primary modules within the `schemas` directory. Each module corresponds to a major feature or component of the Athomic Layer.

-   **`app_settings.py`**: The main Pydantic model that aggregates all other configuration models.

-   **`context/`**:
    -   `context_config.py`: Defines settings for the **[Context Management](../context.md)** module, including which variables to propagate.

-   **`control/`**:
    -   `control_config.py`: Root model for runtime control features.
    -   `feature_flags_config.py`: Schemas for the **[Feature Flags](../control/feature_flags.md)** system.
    -   `live_config.py`: Schemas for the **[Live Configuration](../control/live_config.md)** watcher and state services.
    -   `scheduler_config.py`: Schemas for the **[Task Scheduler](../control/scheduler.md)**.

-   **`database/`**:
    -   `database_config.py`: Main model for all **[Data & Persistence](../database.md)** connections.
    -   `document/`: Schemas for **[Document Store](../database/documents.md)** providers (e.g., MongoDB).
    -   `kvstore/`: Schemas for **[Key-Value Store](../database/kvstore.md)** providers (e.g., Redis) and their wrappers.
    -   `migrations_config.py`: Schemas for the **[Database Migrations](../database/migrations.md)** engine.

-   **`events/`**:
    -   `events_config.py`: Schemas for the **[Internal Event Bus](../events.md)**.

-   **`http/`**:
    -   `http_config.py`: Schemas for the **[Resilient HTTP Client](../http.md)**.

-   **`integration/`**:
    -   `integration_config.py`: Root model for all external integrations.
    -   `consul_config.py`: Schemas for the **[Consul Client](../integration/consul.md)**.
    -   `discovery_config.py`: Schemas for the **[Service Discovery](../integration/discovery.md)** system.
    -   `messaging/`: A rich set of schemas for the **[Messaging](../integration/messaging/index.md)** module, including producer, consumer, DLQ, and republisher settings.
    -   `tasks/`: Schemas for **[Background Task](../integration/tasks.md)** brokers.

-   **`lineage/`**:
    -   `lineage_config.py`: Defines settings for the **[Data Lineage](../lineage.md)** module. Now includes:
        -   `LineageProducerSettings`: Identity configuration.
        -   `LineageStoreSettings`: Composite storage configuration.
        -   Specific backend settings (`DocumentLineageStoreSettings`, `GraphLineageStoreSettings`, etc.).

-   **`observability/`**:
    -   `observability_config.py`: Main model for the observability stack.
    -   `log/logging_config.py`: Schemas for **[Structured Logging](../observability/log.md)**.
    -   `metrics/metrics_config.py`: Schemas for **[Prometheus Metrics](../observability/metrics.md)**.

-   **`performance/`**:
    -   `performance_config.py`: Root model for performance features.
    -   `cache_config.py`: Schemas for the **[Caching](../performance/cache.md)** system.
    -   `compression_config.py`: Schemas for **[HTTP Compression](../performance/compression_middleware.md)**.

-   **`resilience/`**:
    -   `resilience_config.py`: The main model that aggregates all resilience patterns.
    -   Contains individual schema files for each pattern (e.g., `retry_config.py`, `circuit_breaker_config.py`).

-   **`security/`**:
    -   `security_config.py`: The main model for all security features.
    -   `auth_config.py`: Schemas for **[Authentication](../security/auth.md)** (JWT, API Key).
    -   `crypto_config.py`: Schemas for **[Cryptography](../security/crypto.md)**.
    -   `secrets/`: Schemas for **[Secrets Management](../security/secrets.md)**.

-   **`serializer/`**:
    -   `serializer_config.py`: Schemas for the **[Serializer](../serializer.md)** module.

-   **`storage/`**:
    -   `storage_config.py`: Schemas for the **[File Storage](../storage.md)** abstraction.