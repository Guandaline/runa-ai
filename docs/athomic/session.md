# Session Management (Leasing & TTL)

## Overview

The **Session module** provides a **generic, domain-agnostic lifecycle and leasing mechanism**
for managing expensive or stateful resources in asynchronous, concurrent systems.

It solves a recurring platform-level problem:

> How do we safely reuse, expire, and clean up resources that are costly to create,
> shared across requests, and require asynchronous shutdown?

Although currently used by the AI Sandbox subsystem, this module is **not sandbox-specific**
and is designed for reuse across the Athomic platform.

---

## Core Concepts

### Session vs Cache vs Pool

A **Session** represents a *leased resource* with explicit ownership semantics:

- Idle-based expiration (TTL)
- Asynchronous cleanup
- Concurrency-safe acquisition
- Deterministic lifecycle

This differs fundamentally from:

- **Caches**, which focus on data eviction
- **Pools**, which focus on capacity management
- **Connections**, which focus on transport reuse

---

## Architecture

The module is intentionally minimal and composed of **two orthogonal building blocks**:

```text
nala/athomic/session/
├── lease.py     # SessionLease[T]: state + TTL + async cleanup
└── manager.py   # SessionManager[T]: orchestration, reuse, GC
```

---

## SessionLease

`SessionLease[T]` represents a **single leased resource instance**.

### Responsibilities

- Track creation and last usage time
- Determine expiration based on idle TTL
- Execute asynchronous cleanup exactly once
- Guarantee idempotent close semantics

### Non-Responsibilities

- No concurrency control
- No scheduling
- No domain-specific logic

---

## SessionManager

`SessionManager[T]` orchestrates the lifecycle of multiple leases.

### Responsibilities

- Ensure at most one resource is created per key concurrently
- Reuse valid, non-expired sessions
- Perform lazy garbage collection on access
- Support explicit garbage collection
- Coordinate safe asynchronous cleanup

### Non-Responsibilities

- No factory ownership
- No configuration storage
- No domain awareness

---

## Design Principles

### Async-First Cleanup

All resource cleanup is asynchronous to support:

- Network calls
- Cloud resource termination
- SDK shutdown
- Process or container cleanup

This avoids blocking shutdown paths and prevents hidden I/O.

---

### Inversion of Control

Factories, TTL values, and cleanup callbacks are **provided at acquisition time**:

- Enables per-request policies
- Avoids global configuration
- Improves testability and reuse

---

### Monotonic Time

Idle expiration relies on `time.monotonic()` instead of wall-clock time,
ensuring correctness across clock drift, NTP adjustments, and container pauses.

---

## Typical Usage

### Acquisition Flow

1. A caller requests a session by key
2. The manager checks for an existing lease
3. If the lease is valid, it is reused
4. If expired, it is closed asynchronously
5. If missing, a new resource is created via the provided factory

---

### Example

```python
from nala.athomic.session.manager import SessionManager

session_manager = SessionManager()

async def get_resource(context_id: str):
    lease = await session_manager.get_or_create(
        key=context_id,
        factory=create_resource_async,
        ttl_seconds=300,
        on_close=close_resource_async,
    )
    return lease.resource
```

---

## Garbage Collection Strategies

The module supports two complementary GC approaches:

### Lazy Garbage Collection

- Performed during `get_or_create`
- Zero background overhead
- Ideal for request-driven systems

### Active Garbage Collection

- Executed via `cleanup_expired()`
- Can be scheduled externally
- Suitable for long-lived services

---

## Shutdown Semantics

Calling `shutdown()` guarantees:

- All active sessions are terminated
- Cleanup callbacks are awaited
- No resource leaks during process shutdown

This makes the module safe to integrate with application lifecycle hooks.

---

## Integration with Sandbox

Within the AI Sandbox subsystem, the Session module is used to:

- Lease sandbox providers per thread or context
- Enforce idle TTL for cost and safety control
- Ensure asynchronous cleanup of cloud resources

All sandbox-specific behavior remains outside this module.

---

## What This Module Does Not Do

This module intentionally avoids:

- Cost accounting
- Metrics aggregation
- Policy enforcement
- Distributed coordination
- Persistent storage

These concerns are handled at higher layers.

---

## API Reference

### SessionLease

```python
nala.athomic.session.lease.SessionLease
```

### SessionManager

```python
nala.athomic.session.manager.SessionManager
```
