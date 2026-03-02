# ADR-006: Choice of `limits` Library for Rate Limiting

* **Status:** Accepted (Implemented)
* **Date:** 2025-04-13 (Note: Using current date as placeholder)

## Context

* **Problem:** APIs, whether public or internal, require protection against abuse (intentional or accidental) and overload. A mechanism is needed to limit the number of requests a client (identified by IP, user, token, etc.) can make within a specific time period. Implementing this logic from scratch is complex, requiring management of counters, time windows (fixed, sliding), and state storage (in-memory, Redis, etc.).
* **Goal:** Adopt a robust, flexible, well-maintained rate limiting solution for `athomic` that integrates well with the project's asynchronous Python architecture, supporting different limiting strategies and storage backends. [source: 184]
* **Alternatives Considered:**
    * **Manual Implementation:** Building all the logic for counting, time windows, and storage internally. *Drawback:* Very complex to get right (especially sliding window algorithms and distributed consistency), high development and maintenance cost, reinvents the wheel.
    * **Framework-Specific Rate Limiting Libraries:** Using solutions coupled to specific web frameworks, like `slowapi` for FastAPI. *Drawback:* Ties the rate limiting logic to the web framework, making it difficult to reuse outside the FastAPI context (e.g., background tasks, internal calls) or to migrate to another framework later.
    * **Other Generic Python Libraries:** Evaluating alternatives like `pyrate-limiter`. *Drawback:* At the time of evaluation, the `limits` library appeared more mature, offering more strategies, support for multiple storage backends [source: 1075], and good documentation.
    * **Rate Limiting at the Infrastructure Level (Gateway/Infra):** Relying solely on rate limiting configured in API Gateways (Kong, Nginx, Cloudflare, etc.) or Load Balancers. *Drawback:* Offers less granularity (can be hard to apply specific limits per authenticated user or per complex operation within the API), the logic resides outside the application, harder to unit test. Often used as a complementary layer, but doesn't replace the need for application-level rate limiting in many scenarios.

## Decision

* Adopt the **`limits`** Python library [source: 4, 12, 220] as the foundation for rate limiting functionality within `athomic`.
* Create a dedicated module **`nala.athomic.rate_limiter`** to encapsulate interaction with the `limits` library.
* Define an **`AbstractRateLimiter`** interface [source: 1065] to standardize interaction with the rate limiting system.
* Implement a **`LimitsRateLimiter`** provider [source: 1099] that utilizes the `limits` library internally. This provider supports:
    * Configurable strategies (`fixed` window, `moving` window). [source: 1099]
    * Multiple storage backends supported by the library, configured via a `storage_uri` [source: 853, 1099] (e.g., `memory://`, `redis://`, `memcached://` [source: 1075]).
* Expose the functionality through:
    * An **`@rate_limited`** decorator [source: 1092] for easy application to async functions.
    * A **`core.py`** module [source: 1076] for more programmatic usage if needed (e.g., in middleware).
* Manage configuration (default backend, strategy, storage URI, key prefix) via the **`RateLimiterSettings`** Pydantic model [source: 853] within the centralized configuration system (ADR-001).

## Consequences

* **Positive:**
    * **Reuses Robust Logic:** Leverages a well-tested and maintained library (`limits`) that correctly implements complex rate limiting algorithms (fixed window, moving/sliding window).
    * **Flexibility of Strategy & Backend:** Allows choosing the limiting strategy and storage backend via configuration without changing application code. [source: 1075, 1099]
    * **Clean Integration:** Using the `AbstractRateLimiter` interface and the `@rate_limited` decorator keeps business logic decoupled from rate limiting implementation details.
    * **Asynchronous Support:** The `limits` library has good support for `asyncio`.
    * **Community & Documentation:** `limits` is reasonably well-established and documented within the Python community.
* **Negative:**
    * **External Dependency:** Adds the `limits` library as a project dependency.
    * **Library Limitations:** `athomic` inherits the features and limitations of the `limits` library. For instance, the difficulty in implementing `clear` for a specific key [source: 1103] is an inherited limitation.
    * **Abstraction Layer:** Creating the `LimitsRateLimiter` wrapper adds a small layer of indirection over the original library.
* **Neutral/Other:**
    * Correct configuration of the `storage_uri` and strategy is crucial for expected behavior in different environments (single-instance vs. multi-instance).
    * Requires developers to understand basic rate limiting concepts (limit, window, strategies) to use the feature effectively.