# Context Management

## Overview

The Context Management module is the backbone for multi-tenancy, distributed tracing, and enriched logging throughout the Athomic Layer. It provides a safe and reliable way to carry request-scoped state through your application without passing arguments down the call stack.

It is built on top of Python's native `contextvars`, making it fully compatible with `asyncio` and ensuring that context is never accidentally shared between concurrent requests or tasks.

### Core Use Cases

-   **Multi-Tenancy**: Automatically isolates data by carrying the `tenant_id` from the initial request to the database layer.
-   **Distributed Tracing**: Propagates `trace_id` and `span_id` across function calls and even to background tasks.
-   **Enriched Logging**: Allows log records to be automatically enriched with contextual data like `request_id` and `user_id`.
-   **Consistent Keying**: Provides a `ContextKeyGenerator` for creating standardized keys for caches, locks, and rate limiters.

---

## Core Components

### `ContextVarManager`

This is the central registry that manages the lifecycle of all context variables. It handles their creation, default values, and tracks which variables should be propagated to background tasks.

### `context_vars` Module

This module defines all the context variables available in the application (e.g., `tenant_id`, `request_id`, `user_id`, `locale`) and provides simple getter and setter functions for each one. This is the primary API you will interact with.

```python
# Example of using the getters and setters
from nala.athomic.context import context_vars

# Set a value (typically in a middleware)
token = context_vars.set_tenant_id("tenant-123")

# Get a value anywhere in the call stack
current_tenant = context_vars.get_tenant_id() # Returns "tenant-123"

# Reset the value (restores the previous state)
context_vars.get_tenant_id().reset(token)
```

### `ExecutionContext`

This is a simple data class that captures a snapshot of all current context variables at a specific moment in time. Its main purpose is to facilitate context propagation.

---

## Context Propagation

One of the biggest challenges in a microservices architecture is maintaining context across different processes, especially when dispatching background tasks. This module provides a simple and effective solution.

1.  **`capture_context()`**: Before a background task is sent to a broker, this function is called. It reads all context variables marked for propagation and returns them in a serializable dictionary.
2.  **`restore_context()`**: On the worker side, this function is used as a context manager (`with restore_context(...)`). It takes the dictionary captured in step 1 and temporarily applies those values to the `contextvars` for the duration of the task execution.

This ensures that a background task for sending an email, for example, will have the same `trace_id` and `tenant_id` as the API request that triggered it.

### Example

```python
# In your API endpoint
from nala.athomic.context import capture_context
from my_app.tasks import send_welcome_email_task

async def create_user(user_data: dict):
    # ... create user ...

    # Capture the current context before enqueuing the task
    context_to_propagate = capture_context()
    
    # Pass the context in the task's keyword arguments
    await send_welcome_email_task.delay(
        user_id=user.id,
        _nala_context=context_to_propagate
    )

# In your worker/task definition
from nala.athomic.context import restore_context
from nala.athomic.integration.tasks import task

@task()
async def send_welcome_email_task(user_id: int, _nala_context: dict):
    # The `run_task_with_context` decorator usually handles this automatically,
    # but this is how it works internally.
    with restore_context(_nala_context):
        # Now, inside this block, get_tenant_id() and get_trace_id()
        # will return the values from the original API request.
        await send_email_to(user_id)
```

*Note: The `@run_task_with_context` decorator automates this process for you.*

---

## Contextual Key Generation

To ensure consistency in caching, locking, and rate limiting, the `ContextKeyGenerator` automatically creates keys that are namespaced and aware of the current context.

A key is typically generated with the following structure:
`static_prefix:context_prefix:namespace:logical_key`

-   **`static_prefix`**: A global prefix (e.g., "nala").
-   **`context_prefix`**: Automatically includes the `tenant_id` and/or `user_id` if enabled in the configuration.
-   **`namespace`**: A logical grouping for the key (e.g., "cache", "ratelimit").
-   **`logical_key`**: The specific identifier for the resource.

```python
from nala.athomic.context import ContextKeyGenerator

# Assume tenant_id='tenant-123' is set in the context
key_gen = ContextKeyGenerator(namespace="cache")
cache_key = key_gen.generate("user-profile", "user-456")

# Result: "nala:tenant-123:cache:user-profile:user-456"
```

---

## API Reference

::: nala.athomic.context.context_vars

::: nala.athomic.context.propagation

::: nala.athomic.context.generator.ContextKeyGenerator

::: nala.athomic.context.execution.ExecutionContext