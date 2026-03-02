# Configuration Management

## Overview

The configuration module is a robust, type-safe system that provides the foundation for all configurable components within the Athomic Layer. It is built upon two key libraries:

-   **Dynaconf**: For layered configuration loading from multiple sources (files, environment variables, Vault, etc.).
-   **Pydantic**: For strict, type-safe validation of the configuration structure at startup.

This combination ensures that the application starts with a valid and predictable configuration, failing fast if any required settings are missing or malformed.

### Key Features

-   **Layered Loading**: Settings are loaded from `.toml` files and can be individually overridden by environment variables.
-   **Environment Switching**: Easily switch between environments (e.g., `development`, `production`) by setting a single environment variable.
-   **Type Safety**: The entire configuration is parsed into a strongly-typed Pydantic model (`AppSettings`), providing auto-completion and static analysis benefits.
-   **Integrated Secret Management**: Handles sensitive values securely, either by reading them directly or by resolving references to external secret managers like Vault at runtime.

---

## How It Works

The configuration is loaded and validated in a two-step process during application startup:

1.  **Loading with Dynaconf**: The `DynaconfLoader` reads all specified `.toml` files, merges them based on the current environment, and then applies any overrides from environment variables.
2.  **Validation with Pydantic**: The raw dictionary loaded by Dynaconf is passed to the root `AppSettings` Pydantic model. Pydantic recursively validates the entire structure, coercing types and raising a `ValidationError` if any part of the configuration is invalid.

### Accessing Settings

The primary way to access configuration throughout the application is via the `get_settings()` function. This function is cached, ensuring that the loading and validation process happens only once.

```python
from nala.athomic.config import get_settings

settings = get_settings()
print(settings.app_name)
print(settings.database.default_document_connection)
```

---

## Configuration Files & Environments

By default, the application loads configuration from `settings.toml`. You can create additional files for different environments, like `development.toml` or `production.toml`.

To activate a specific environment, set the `NALA_ENV_FOR_DYNACONF` environment variable. Dynaconf will then automatically merge the base `settings.toml` with the environment-specific file.

```bash
export NALA_ENV_FOR_DYNACONF=production
# The application will now load settings from settings.toml and merge them with production.toml
```

---

## Environment Variables Override

Any setting can be overridden using environment variables. This is particularly useful for containerized deployments (e.g., Docker, Kubernetes).

-   **Prefix**: All variables must start with `NALA_`.
-   **Separator**: Nested keys are separated by a double underscore `__`.

For example, to override the database name for the default MongoDB connection, you would set the following environment variable:

```bash
export NALA_DATABASE__DOCUMENTS__DEFAULT_MONGO__PROVIDER__DATABASE_NAME="my_production_db"
```

---

## Secret Management

The configuration system has first-class support for handling secrets securely.

### 1. Direct Value (from Environment)

For secrets provided directly as environment variables, you can use Pydantic's `SecretStr` type in the configuration model. This ensures the value is automatically masked when logged or printed.

### 2. Secret Reference (from Vault, etc.)

For a more secure approach, you can configure a reference to a secret stored in an external manager. This is done using the `SecretValue` model, which requires a `path` and a `key`.

```toml
# In your settings.toml
[default.database.documents.default_mongo.provider]
# This does not contain the actual password.
# It's a reference to a secret stored in Vault at path 'database/mongo' with key 'password'.
password = { path = "database/mongo", key = "password" } # pragma: allowlist secret
```

At startup, the `SecretsManager` traverses the entire configuration and replaces these `SecretValue` objects with a lazy-loading proxy. The actual secret is only fetched from the provider (e.g., Vault) at the moment it is first needed.

---

## API Reference

::: nala.athomic.config.get_settings

::: nala.athomic.config.schemas.app_settings.AppSettings

::: nala.athomic.config.schemas.models.SecretValue