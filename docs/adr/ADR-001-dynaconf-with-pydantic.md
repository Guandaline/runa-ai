# ADR-001: Use of Dynaconf + Pydantic for Configuration Management

* **Status:** Accepted (Implemented)
* **Date:** 2025-04-13 (Note: Ideally, use the date the decision was made)

## Context

* **Problem:** Modern applications need to manage complex configurations (database, cache, external services, feature flags) that vary across environments (development, testing, production). Using only environment variables or simple files (`.ini`, `.json`) becomes difficult to manage, validate, and ensure correct typing.
* **Needs:**
    * Load configurations from multiple sources (files like `.toml`, `.env`, environment variables, and potentially Vault in the future [source: 9]).
    * Separate configurations by environment (`default`, `development`, `production`). [source: 18, 20, 21, 22]
    * Rigorously validate configuration values and structure at startup to prevent runtime errors. [source: 235]
    * Provide type-safe access to configurations within the application code.
* **Alternatives Considered:**
    * **Pure Environment Variables:** Simple, but impractical for nested structures and lacks intrinsic validation/typing.
    * **Pydantic `BaseSettings`:** Excellent for validation and typing, but more limited in loading sources (focuses on env vars and `.env`).
    * **`.ini`/`.json` files + `ConfigParser`/`json`:** Less expressive than TOML for complex structures, lack strong integrated validation.
    * **Python Modules (`config.py`):** Difficult to override externally (via env vars) and can violate the separation of code and configuration.

## Decision

* Adopt the **`Dynaconf`** library as the primary configuration loader, leveraging its ability to read and merge multiple sources and environments. [source: 4, 775-792]
* Utilize **`.toml`** files to define default configurations and environment-specific overrides (`settings/settings.toml`, `settings/development.toml`, `settings/production.toml`). [source: 18, 20-22]
* Allow the use of **`.env`** files for local overrides or secrets during development. [source: 17, 784]
* Allow **environment variables** (prefixed with `NALA_` [source: 775]) to override any values defined in the files.
* Define the entire expected configuration structure using **`Pydantic` models** (starting with `AppSettings` [source: 817] and including nested models like `CacheSettings` [source: 845], `SecretsSettings` [source: 820], `DatabaseSettings` [source: 846], etc.). [source: 767]
* Implement a centralized access point (`nala.athomic.config.settings.get_settings`) [source: 768] that:
    1. Uses `DynaconfLoader` [source: 769] to load raw configuration data into a dictionary.
    2. Validates this dictionary against the `AppSettings` Pydantic model. [source: 771-774]
    3. Returns the validated, type-safe instance of `AppSettings`.
    4. Utilizes `@lru_cache` [source: 712, 768] to ensure loading and validation occur only once.

## Consequences

* **Positive:**
    * **Flexibility:** Configuration loading from diverse sources with clear precedence (env var > .env > environment file > default file).
    * **Early Validation:** Configuration errors (wrong types, missing values) are caught at application startup, not at runtime.
    * **Type Safety:** Accessing configurations in code (e.g., `settings.cache.ttl`) is type-safe, aided by type hints and IDE auto-completion.
    * **Clear Structure:** The configuration structure is explicitly defined and documented by the Pydantic models.
    * **Maintainability:** Facilitates refactoring and understanding of available configurations.
    * **Extensibility:** Prepared for adding new sources (like Vault) in the future, integrating them with Dynaconf or as additional providers validated by Pydantic.
* **Negative:**
    * **Dependencies:** Adds two significant dependencies (`Dynaconf`, `Pydantic`) to the project.
    * **Learning Curve:** Requires familiarity with Dynaconf's loading rules and Pydantic model definition/validation.
    * **Dual Definition:** It's necessary to maintain the structure in both the `.toml` files and the Pydantic models (although aliases help [source: 818, 824]).
* **Neutral/Other:**
    * Configuration is loaded and validated once at the start (due to `@lru_cache`), making subsequent access very fast but requiring an application restart to reflect changes (unless a live-reload mechanism is implemented).