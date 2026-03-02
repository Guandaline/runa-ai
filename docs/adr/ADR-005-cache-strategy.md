# ADR-005: Advanced Caching Strategy with Decorators and Multiple Backends

* **Status:** Accepted (Implemented)
* **Date:** 2025-04-13 (Note: Using current date as placeholder)

## Context

* **Problem:** In distributed systems and high-load APIs, frequent access to slow data sources (databases, external service calls) can become a significant performance and availability bottleneck. Simple caching helps, but doesn't address common large-scale caching issues, such as:
    * **Cache Stampede (Thundering Herd):** Multiple concurrent requests/processes attempting to recalculate an expired cache value simultaneously, overwhelming the underlying data source.
    * **Expiration Latency:** When a cached item expires, the next request needing it must wait for the recalculation time, increasing perceived latency.
    * **Need for Multiple Backends & Fallback:** The requirement to use different cache types (e.g., local in-memory for ultra-fast access of small/frequent data, Redis for distributed/persistent cache) and having a fallback strategy if the primary cache fails. 
    * **Code Clutter:** Manually implementing cache checking, storage, and invalidation logic within business functions pollutes the core logic, making it repetitive and error-prone.
* **Goal:** Implement a robust, flexible, and easy-to-use caching system for `athomic` that mitigates the problems above, offers high performance and resilience, and integrates cleanly into the codebase, preferably via decorators.
* **Alternatives Considered:**
    * **Manual Caching:** Requiring developers to manually implement `cache.get()`, `compute_value()`, `cache.set()` logic at each necessary point. *Drawback:* Highly repetitive, error-prone, difficult to maintain consistency, doesn't easily accommodate advanced features.
    * **Simple Caching (Get/Set Only):** Implementing only basic cache operations. *Drawback:* Fails to solve cache stampede or abrupt expiration issues.
    * **Direct Use of Caching Libraries:** Using libraries like `cachetools` or the `redis-py` client directly within business logic. *Drawback:* Would require manual implementation of Jitter, Locking, Refresh Ahead, Fallback logic, and integration with configuration/observability.
    * **Web Framework Caching (HTTP Level):** Relying solely on framework mechanisms for caching full HTTP responses. *Drawback:* Less granular, not applicable to internal calculations or service calls, doesn't cache raw data or intermediate results effectively.

## Decision

* Implement the **`nala.athomic.performance.cache`** module following the Provider/Registry/Factory pattern (ADR-003) to support multiple backends.
* Initially support **`MemoryCacheProvider`** (based on `cachetools.TTLCache`) and **`RedisCacheProvider`** (using async `redis-py`), both adhering to the `CacheProtocol` interface.
* Implement a **`FallbackCacheProvider`** allowing a configurable chain of providers (e.g., try Redis, if it fails, try Memory), enhancing resilience. 
* Create a primary decorator **`@cache_result`**  as the main way to apply caching to (async) functions.
* Embed advanced features within `@cache_result`, controllable via parameters:
    * **`ttl`:** Configurable time-to-live for the cached item.
    * **`use_jitter`:** Apply random variation (jitter) to the final TTL (`apply_jitter`) to prevent mass simultaneous expirations.
    * **`use_lock`:** Implement a lock (mutex) mechanism per cache key to prevent cache stampedes. Only the first request/task hitting an expired/missing key acquires the lock to recompute; others wait for the result or lock release. (Note: Current implementation uses `asyncio.Lock`, only safe for single-instance).
    * **`refresh_ahead`:** Allow the value to be recomputed in the background *before* it expires (based on `refresh_threshold`). Current requests receive the old (stale) value while the new one is generated, ensuring low latency. The recomputed value replaces the old one for subsequent requests. 
* Create an **`@invalidate_cache`** decorator to easily remove specific cache keys before a function executes (useful after write/update/delete operations).
* Implement a **`hash_key`** utility  to generate deterministic, unique cache keys based on the cached function's name, arguments (`*args`, `**kwargs`), and a configurable prefix (global or per-decorator), avoiding collisions.
* Integrate the caching system with the **Observability** module by emitting Prometheus metrics for cache hits, misses, and errors (`cache_hit_counter`, `cache_miss_counter`, `cache_error_counter`) via a wrapper function like `observed_get`. 

## Consequences

* **Positive:**
    * **Significant Performance Improvement:** Reduces latency and load on slower backend data sources for frequently accessed data.
    * **High Resilience & Availability:** Mitigates cache stampedes (with `use_lock`), smooths out cache expiration impacts (with `refresh_ahead`, `use_jitter`), and increases overall availability via `FallbackCacheProvider`.
    * **Cleaner & Declarative Code:** Caching complexity is encapsulated within the decorators and the `athomic.cache` module, keeping business logic focused.
    * **Ease of Use:** Applying advanced caching strategies becomes as simple as adding and configuring the `@cache_result` decorator to an async function.
    * **Granular Configurability:** Developers control TTL, expiration strategies (jitter), stampede protection (lock), proactive updates (refresh ahead), backends, and fallbacks via configuration and decorator parameters.
    * **Integrated Observability:** Built-in metrics provide visibility into cache effectiveness and health.
* **Negative:**
    * **Intrinsic Complexity:** The cache module itself is relatively complex due to the combination of advanced features.
    * **Cache Consistency Management:** As with any caching system, correct cache invalidation (using `@invalidate_cache` or other strategies) is crucial to avoid serving stale data after the underlying data has been modified. The `refresh_ahead` strategy intentionally serves stale data for a short period.
    * **Debugging Challenges:** The introduction of state (the cache) and asynchronous background logic (refresh ahead) can occasionally make debugging certain flows more complex.
    * **Distributed Lock Required for Scale:** The `use_lock=True` feature in the current implementation (`asyncio.Lock` [source: 766]) only provides stampede protection within a single application instance. For a multi-instance deployment, a distributed lock implementation (e.g., using Redis) would be required for this feature to be fully effective (not currently implemented).
* **Neutral/Other:**
    * The effectiveness of the cache fundamentally depends on choosing the right operations to cache, setting appropriate TTLs, and having a well-thought-out cache invalidation strategy.