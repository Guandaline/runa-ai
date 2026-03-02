# ADR-002: Creation of the `athomic` Abstraction Layer

* **Status:** Accepted (Implemented)
* **Date:** 2025-04-13 (Note: Ideally, use the date the decision was made)

## Context

* **Problem:** Modern APIs rely heavily on cross-cutting infrastructure concerns like caching, configuration management, secrets handling, rate limiting, logging, observability, and resilience patterns (retry, fallback). Mixing this logic directly with the API endpoint handlers (e.g., in FastAPI routes) or business logic leads to high coupling, code duplication, difficulty in testing, and hinders reusability across different projects or API frameworks.
* **Goal:** Create a reusable, framework-agnostic core library (`athomic`) that encapsulates these infrastructure best practices, allowing application developers to focus on business logic. [source: 7, 15, 16]
* **Alternatives Considered:**
    * **No Abstraction:** Implement infrastructure logic directly within the API framework (e.g., using FastAPI dependencies and middleware). *Drawback:* High coupling to the framework, poor reusability, harder testing.
    * **Utility Functions:** Place infrastructure logic in simple utility functions. *Drawback:* Less organized, harder to enforce consistency, doesn't easily support stateful components or different providers.
    * **Multiple Smaller Libraries:** Create separate libraries for cache, secrets, etc. *Drawback:* Increases dependency management overhead, harder to ensure cohesive integration and consistent patterns across libraries.

## Decision

* Create a distinct top-level Python package named **`nala.athomic`** within the `src/nala/` directory. [source: 8]
* This `athomic` layer will house all core, reusable infrastructure components, designed to be as independent as possible from specific web frameworks (like FastAPI).
* Sub-modules within `athomic` will be organized by concern: `cache`, `config`, `db`, `log` (safelogger), `observability`, `rate_limiter`, `security`, `service_discovery`, `utils`. [source: 8-10, 689-1127]
* Components within `athomic` will primarily expose functionality through well-defined interfaces (Protocols/ABCs) [source: 443, 689, 855, 918, 1000, 1065] and decorators [source: 445, 726-735, 942-959, 962, 1092].
* The `nala.api` layer (containing FastAPI specifics like routes, middleware, request/response models) will *depend on* and *consume* the services provided by the `nala.athomic` layer.

## Consequences

* **Positive:**
    * **High Reusability:** `athomic` components can potentially be reused in other Python applications or services, not just FastAPI APIs. [source: 14, 16]
    * **Improved Testability:** Core infrastructure logic in `athomic` can be tested independently of the web framework, often with simpler unit tests.
    * **Clear Separation of Concerns:** Enforces a clean architecture, separating infrastructure logic from API handling and business rules.
    * **Enhanced Maintainability:** Changes to infrastructure (e.g., switching cache providers) are localized within `athomic`, minimizing impact on the API layer.
    * **Scalability:** Promotes building specialized, robust core components.
* **Negative:**
    * **Increased Indirection:** Adds a layer of abstraction, which might slightly increase complexity for simple use cases or for developers unfamiliar with the structure.
    * **Potential for Over-Engineering:** Need to be mindful not to abstract prematurely or create overly complex interfaces if the benefit isn't clear.
* **Neutral/Other:**
    * Requires clear documentation explaining the purpose and usage of the `athomic` layer and its components. [source: 7-16, 175-616]
    * Establishes a strong architectural pattern that should guide future development within the `athomic` ecosystem.