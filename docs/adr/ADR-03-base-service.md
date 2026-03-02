# ADR-030: Adopt a BaseService Class for Stateful Components

**Status:** Accepted
**Date:** 2025-06-26

---

## Context

During the development of `nala.athomic`, it was observed that multiple components managing an external connection or internal state (e.g., `Producer`, `Consumer`, `CacheProvider`) needed to implement repetitive and complex logic for:

1.  **Lifecycle Management:** Orchestrating `connect()` and `close()` operations.
2.  **Concurrency Control:** Using `asyncio.Lock` to prevent `connect()` and `close()` from being called concurrently.
3.  **State Management:** Maintaining flags like `_connected`, `_is_closed` to track the service's current state.
4.  **Observability:** Emitting standardized Prometheus metrics and structured logs for connection attempts, failures, and status.
5.  **Readiness Signaling:** Informing the rest of the application when the service is fully initialized and ready to handle traffic.

The absence of a centralized pattern was leading to code duplication, implementation inconsistencies, and increased complexity in maintenance and testing.

---

## Decision

We have decided to introduce a **Base Service** pattern for all stateful components within `nala.athomic`. This pattern consists of two main parts:

1.  **`nala.athomic.base.ServiceProtocol`**: An interface contract that defines the public signature of a manageable service (`connect`, `close`, `is_ready`, `is_enabled`, `health`). Code that consumes a service should depend on this protocol, not on a concrete implementation.

2.  **`nala.athomic.base.BaseService`**: An **abstract** base class that implements the `ServiceProtocol` and provides all the common logic for orchestrating lifecycle, state, concurrency, and observability.

Subclasses (like `KafkaConsumer`) now inherit from `BaseService` and only need to implement the abstract `_connect()` and `_close()` methods with technology-specific logic, inheriting all the remaining robust behavior.

---

## Consequences

### Positive

- **Consistency and Standardization:** All services will have an identical and predictable lifecycle and state behavior.
- **Reduced Boilerplate:** Eliminates the need to rewrite complex logic for locks, `try/except/finally` blocks, state flags, and metrics in every new component.
- **Observability by Default:** Any new service inheriting from `BaseService` automatically gains connection and readiness metrics, as well as structured logs.
- **Improved Developer Experience (DX):** Makes the creation of new, robust components significantly faster and less error-prone.
- **Enhanced Reliability:** The lifecycle logic, being centralized, can be rigorously tested in a single place.

### Negative

- **Coupling to the Base Class:** Subclasses now have a direct coupling to `BaseService`. Although this is mitigated by using the `ServiceProtocol` in the service's consumers, the implementation itself is tied to inheritance.
- **Learning Curve:** New developers must first learn the `BaseService` pattern before they can contribute new stateful components, rather than creating them ad-hoc.