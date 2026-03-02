# ADR-107: AI Governance and Observability Architecture

* **Status:** Accepted
* **Date:** 2025-12-04

## Context

Interacting with Large Language Models (LLMs) introduces specific challenges compared to standard external API calls:
1.  **Non-determinism & Latency:** LLM calls are slow and variable. We need deep visibility into duration, token usage, and model parameters to optimize performance and costs.
2.  **Security & Compliance:** We must ensure that sensitive data (PII) is not sent to third-party providers and that usage complies with internal quotas and budgets.
3.  **Provider Diversity:** We use multiple providers (OpenAI, Vertex AI). Implementing logging, metrics, and safety checks individually for each provider leads to code duplication and inconsistent enforcement.

We needed a pattern that guarantees these cross-cutting concerns are addressed for *every* call, regardless of the underlying provider implementation.

## Decision

We decided to implement the **Template Method Design Pattern** combined with an **Interceptor (Guard) Pattern** to enforce governance and observability at the base abstraction level.

### 1. Template Method in Base Classes
We implemented abstract base classes (`BaseLLM`, `BaseEmbedding`) that define the public-facing methods (e.g., `generate_content`) as "templates".

These template methods are responsible for the standard execution flow:
1.  **Readiness Check:** Ensures the service is initialized.
2.  **Tracing Initialization:** Starts an OpenTelemetry span with standard semantic attributes (`llm.model`, `llm.provider`, `llm.system`).
3.  **Guard Execution:** Iterates through configured `AIGuardProtocol` instances (Interceptors) to validate the request *before* sending it.
4.  **Delegation:** Calls the abstract protected method (e.g., `_generate_content`) which must be implemented by concrete provider classes to handle the specific API logic.
5.  **Metrics Recording:** Records duration and operation counts (`llm_operations_total`) in a `finally` block to capture both successes and failures.

### 2. Governance Guards
We defined the `AIGuardProtocol` to standardize safety checks. Guards act as middleware that can inspect the prompt and metadata.
* **RateLimitGuard:** Adapts the centralized `RateLimiterService` to the AI context, allowing limits to be scoped by user, tenant, or model family.

```python
# Example of the Template Method implementation
async def generate_content(self, prompt: str, **kwargs):
    # 1. Observability Start
    with self.tracer.start_as_current_span("llm.generate") as span:
        try:
            # 2. Governance
            await self._run_guards(prompt, **kwargs)

            # 3. Provider Execution (Abstract)
            result = await self._generate_content(prompt, **kwargs)

            return result
        finally:
             # 4. Metrics
             self._record_metrics(...)
```

## Consequences

* **Positive:**
    * **Guaranteed Consistency:** It is impossible to implement a new LLM provider in the system without inheriting the base class, which automatically enforces logging, tracing, and metrics standards.
    * **Centralized Governance:** Security policies (like PII filtering or rate limiting) are configured globally and applied to all providers. Changing a policy requires updating only the Guard configuration, not every provider integration.
    * **Vendor-Agnostic Telemetry:** Metrics are normalized (e.g., standard token counting attributes), making it easier to build unified dashboards for cost and performance monitoring across different vendors.

* **Negative:**
    * **Latency Overhead:** Executing a chain of guards adds a small latency penalty to every request. While usually negligible compared to LLM inference time, extensive text analysis guards (e.g., PII scanning) could become a bottleneck.
    * **Implementation Rigidity:** Concrete providers are forced to adhere strictly to the base class structure. If a provider has a radically different interaction model that doesn't fit the `generate_content` template, the abstraction might become leaky or restrictive.

* **Neutral/Other:**
    * **Token Usage Dependency:** Accurate cost tracking relies on the underlying provider returning usage metadata (prompt/completion token counts). If a provider API changes or omits this data, the base class metrics will be incomplete.