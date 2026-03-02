# ADR-009: Implementation of Resilience Patterns via Decorators

* **Status:** Accepted (Implemented for Retry and Fallback; Circuit Breaker/Timeout Planned)
* **Date:** 2025-04-13 (Placeholder)

## Context

* **Problem:** Network requests, database calls, and interactions with external services are inherently unreliable in distributed systems. Transient failures (network glitches, temporary service unavailability, brief resource contention) and persistent failures can occur. Applications need strategies to handle these failures gracefully to avoid cascading failures, improve user experience, and maintain overall system stability. Implementing logic for retrying operations, falling back to alternative data sources or logic paths, or preventing repeated calls to failing services (circuit breaking) directly within the primary business logic flow makes the code verbose, repetitive, error-prone, and harder to read and test.
* **Goal:** Provide reusable, declarative, and minimally invasive mechanisms within `athomic` to apply common resilience patterns (specifically Retry and Fallback initially, with plans for Circuit Breaker and Timeout) to function calls, particularly those involving I/O or external dependencies.
* **Alternatives Considered:**
    * **Manual Implementation:** Developers manually write `try...except` blocks with retry loops, sleep intervals, or conditional fallback logic within each function that needs resilience. *Drawback:* Highly repetitive, difficult to ensure consistency in retry strategies (e.g., backoff timing), error-prone, significantly clutters business logic.
    * **Utility Functions/Classes (Wrappers):** Creating helper functions or context managers that accept the function to be executed and apply retry/fallback logic around it. *Drawback:* Can still be somewhat verbose to apply, requires passing callables around, less declarative than decorators.
    * **Aspect-Oriented Programming (AOP) Frameworks:** Utilizing more heavyweight AOP frameworks (less common in the Python ecosystem compared to Java/C#). *Drawback:* Introduces significant complexity, potentially adds "magic" that obscures control flow, likely overkill for these specific patterns.
    * **Infrastructure-Level Resilience:** Relying solely on retry/fallback mechanisms provided by service meshes (like Istio), API gateways, or load balancers. *Drawback:* Operates at a coarser granularity (HTTP requests), lacks application-specific context (e.g., cannot easily fall back to reading from a cache or using a default value computed by application logic), moves resilience logic outside the application's direct control and testing scope. Often better used as a complementary layer.

## Decision

* Implement core resilience patterns primarily as **Python decorators**, residing in `nala.athomic.utils.decorators`. [source: 942] This approach offers a declarative syntax that separates the resilience concern from the function's core logic.
* **Retry Pattern:**
    * Implement a `@retry_handler.with_retry()` decorator. [source: 944]
    * Leverage the robust and well-maintained **`tenacity`** library [source: 4] internally to handle the retry logic (e.g., `stop_after_attempt`, `wait_exponential`, `retry_if_exception_type`). [source: 946]
    * Make the decorator configurable regarding the number of attempts, wait strategy/timing, and the specific exceptions that should trigger a retry. [source: 943-946]
    * Integrate basic logging to indicate when retries are occurring. [source: 946, 947]
* **Fallback Pattern:**
    * Implement a `@fallback_handler()` decorator [source: 950] that accepts a list of one or more fallback functions as arguments. [source: 953]
    * If the decorated function raises an exception, the decorator will iterate through the provided fallback functions, calling them sequentially until one executes successfully (without raising an exception). [source: 951, 955-958]
    * The decorator must correctly handle both **synchronous and asynchronous** decorated functions and fallback functions, inspecting them to determine whether `await` is needed. [source: 954-959]
    * If the original function and all provided fallback functions fail, the decorator will raise a custom `FallbackError` exception [source: 950] containing the list of all encountered errors for diagnostic purposes. [source: 146, 149]
* **Circuit Breaker & Timeout Patterns:** Recognize these as essential resilience patterns but **defer their implementation** for now. They are noted in the project backlog [source: 186, 219, 591]. The intention is to implement them using a similar decorator-based approach in the future when prioritized.
* **Usage:** Encourage the application of these decorators primarily to methods within the `athomic` layer that interact with external systems (e.g., database repository methods, secret provider `get_secret` calls [source: 871, 876, 888], cache provider interactions) and potentially in the `api` service layer for coordinating calls that might fail.

## Consequences

* **Positive:**
    * **Improved Code Readability & Focus:** Business logic within decorated functions remains clean and focused on its primary responsibility, as the resilience logic is handled declaratively by the decorator.
    * **Reduced Boilerplate:** Significantly reduces the need for repetitive `try...except` blocks and manual retry/fallback logic throughout the codebase.
    * **Consistency:** Promotes a standardized and consistent way of implementing retry and fallback mechanisms across the application.
    * **Reusability:** Decorators are highly reusable components that can be applied to any compatible function (sync/async depending on the decorator).
    * **Configurability:** The behavior of retries (attempts, backoff, specific exceptions) and the fallback chain are configurable per usage.
    * **Leverages Existing Library:** The retry implementation benefits from the robustness and features of the `tenacity` library.
* **Negative:**
    * **Decorator Implementation Complexity:** The decorators themselves, particularly `@fallback_handler` which needs to correctly manage both sync and async functions [source: 954-959], have non-trivial implementation logic.
    * **Potential Obscurity ("Magic"):** For developers unfamiliar with decorators or the specific implementation, the added behavior might seem implicit or "magical". Clear documentation and naming are crucial.
    * **Debugging:** Debugging issues *within* the decorator's execution flow can sometimes be less straightforward than debugging inline code.
    * **Incomplete Resilience Suite (Currently):** The critical patterns of Circuit Breaker and Timeout are currently missing from the implemented set, requiring future work to achieve a more comprehensive resilience strategy. [source: 186]
* **Neutral/Other:**
    * Requires developers to understand when and where it's appropriate to apply the `@retry_handler` versus the `@fallback_handler` (or potentially both, though careful consideration of interaction is needed).
    * The effectiveness of the fallback pattern is entirely dependent on the logic provided within the fallback functions; they must provide a meaningful alternative or default.