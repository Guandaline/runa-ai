# ADR-003: Provider/Registry/Factory Pattern for Extensibility

* **Status:** Accepted (Implemented in several modules)
* **Date:** 2025-04-13 (Note: Ideally, use the date the decision was made)

## Context

* **Problem:** The `athomic` needs to interact with various external systems or support multiple strategies for core functionalities (e.g., different cache backends like Redis/Memory [source: 715, 716]; different secrets managers like Vault/AWS/Local [source: 873, 898]; different auth methods; different rate limiting storages [source: 1075]; different databases [source: 1007]). Hardcoding specific implementations would make the system rigid, difficult to test, and hard to extend or adapt to different deployment environments or future technologies.
* **Goal:** Allow easy swapping and addition of implementations for key infrastructure components without modifying the core consuming logic. Enable configuration-driven selection of implementations. Promote testability by allowing mock providers to be injected. [source: 14, 16]
* **Alternatives Considered:**
    * **Conditional Logic (if/else):** Directly checking configuration values in the code and executing different logic paths. *Drawback:* Violates Open/Closed Principle, leads to complex conditional blocks, hard to add new options.
    * **Strategy Pattern (Simple):** Using classes for strategies but without a central registry or factory. *Drawback:* Requires manual instantiation and passing of the correct strategy class throughout the application, configuration logic might be scattered.
    * **Dependency Injection Framework:** Using a full DI framework (like `python-dependency-injector`). *Drawback:* Adds a potentially heavier dependency, might be overkill if the primary need is swappable providers based on simple configuration keys.

## Decision

* Implement a consistent **"Provider/Registry/Factory" pattern** for key extensible components within the `athomic` layer (Cache, Secrets, Auth, Rate Limiting, DB Repositories, potentially Config loading itself).
* **Provider (Interface):** Define a clear interface (using `abc.ABC` or `typing.Protocol`) for each component, specifying the required methods and their signatures (e.g., `CacheProtocol`, `SecretsProvider`, `AuthProvider`, `AbstractRateLimiter`, `IRepository`). [source: 443, 689, 855, 918, 1000, 1065]
* **Provider (Implementations):** Create concrete classes that implement these interfaces for specific technologies or strategies (e.g., `RedisCacheProvider` [source: 739], `VaultSecretsProvider` [source: 898], `JWTAuthProvider` [source: 929], `LimitsRateLimiter` [source: 1099], `MongoUserRepository` [source: 1030]).
* **Registry (Optional but common):** Maintain a mapping (often a simple dictionary) from a configuration key (e.g., backend name like "redis", "vault") to the corresponding Provider *class* (e.g., `SecretsRegistry` [source: 857], `STORAGE_REGISTRY` in rate limiter [source: 1075]). This centralizes the knowledge of available implementations.
* **Factory (often Singleton):** Create a factory function (e.g., `get_cache` [source: 712], `get_secrets_provider` [source: 859], `get_repository` [source: 1009], `get_auth_provider` [source: 938]) responsible for:
    1. Reading the relevant configuration (via `get_settings`).
    2. Determining the desired provider implementation based on the configuration key (using the Registry if applicable).
    3. Instantiating the chosen Provider class, passing necessary configuration.
    4. Often using `@lru_cache` to return a singleton instance of the configured provider, ensuring efficiency and consistent state.

## Consequences

* **Positive:**
    * **High Extensibility:** Adding support for a new backend (e.g., a new cache provider) involves creating a new class implementing the interface and registering it, with minimal changes to consuming code.
    * **Configurability:** The active provider is determined by configuration settings, allowing easy adaptation to different environments (e.g., use `MemoryCache` in tests, `RedisCache` in production).
    * **Improved Testability:** Consuming code depends on the interface, making it easy to inject mock providers during unit testing.
    * **Decoupling:** Core logic interacts with the interface, unaware of the specific implementation details.
    * **Consistency:** Provides a standard way to handle pluggable components across the framework.
* **Negative:**
    * **Boilerplate:** Introduces some boilerplate code (interfaces, registries, factories) for each extensible component.
    * **Indirection:** Adds a layer of indirection compared to direct instantiation.
* **Neutral/Other:**
    * Relies heavily on the configuration system (ADR-001) being robust.
    * Requires developers to understand the pattern and where to register new providers.