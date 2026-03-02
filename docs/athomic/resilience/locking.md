# Distributed Locking

## Overview

Distributed Locking is a resilience pattern that provides a mechanism for **mutual exclusion** across multiple processes or service instances. It ensures that only one process can execute a critical section of code at a time for a specific, shared resource.

This is essential for preventing race conditions in distributed systems. For example, if two requests try to update a user's account balance at the same time, a distributed lock can ensure that these operations happen sequentially, not concurrently, thus preventing data corruption.

The Athomic implementation provides a simple yet powerful `@distributed_lock` decorator to protect any asynchronous function.

### Key Features

-   **Declarative Use**: Protect critical sections of code with a simple decorator.
-   **Dynamic Key Resolution**: Lock keys can be dynamically generated from the arguments of the decorated function.
-   **Multiple Backends**: Supports a distributed Redis backend for production and a local in-memory backend for testing.
-   **Deadlock Prevention**: Locks are configured with a timeout, ensuring they are automatically released even if a process crashes.

---

## How It Works

1.  **Decorator**: You apply the `@distributed_lock(key="...", timeout=...)` decorator to an `async` function.
2.  **Key Resolution**: When the decorated function is called, the `key` template string is formatted using the function's arguments. For example, a key of `"user-balance:{user_id}"` for a function call with `user_id=123` will resolve to `"user-balance:123"`.
3.  **Acquisition Attempt**: The system then attempts to acquire a lock for this resolved key from the configured provider (e.g., Redis). It will wait for up to the specified `timeout`.
4.  **Execution**: If the lock is acquired, the original function is executed. Once the function completes (either by returning or raising an exception), the lock is **always** released automatically.
5.  **Failure**: If the lock cannot be acquired within the timeout (because another process holds it), a `LockAcquisitionError` is raised immediately, and the function is not executed.

---

## Available Providers

-   **`RedisLockProvider`**: The recommended provider for production. It uses Redis's atomic operations to implement a reliable, distributed lock. It reuses the application's main `KVStore` client for the connection.
-   **`LocalLockProvider`**: An in-memory lock provider that uses `asyncio.Lock`. It is suitable for single-process applications or for running tests without external dependencies. It is **not** distributed.

---

## Usage Example

Imagine a function that needs to safely deduct a value from a user's balance.

```python
from nala.athomic.resilience.locking import distributed_lock, LockAcquisitionError

class BalanceService:
    @distributed_lock(key="balance:{user_id}", timeout=10)
    async def deduct_from_balance(self, user_id: str, amount: float):
        """
        Safely deducts from a user's balance. Only one process can
        execute this for the same user_id at a time.
        """
        current_balance = await db.get_balance(user_id)
        if current_balance < amount:
            raise ValueError("Insufficient funds.")
        
        await db.set_balance(user_id, current_balance - amount)

async def handle_payment(user_id: str, amount: float):
    try:
        await balance_service.deduct_from_balance(user_id, amount)
    except LockAcquisitionError:
        # This occurs if another request for the same user is already processing.
        # You can ask the client to retry the request.
        print("Could not process payment at this time, please try again.")
```

---

## Configuration

The locking provider is configured under the `[resilience.locking]` section in your `settings.toml`.

```toml
[default.resilience.locking]
enabled = true

# The default time in seconds a lock is held before it automatically expires.
lock_timeout_sec = 30

  # Configure the backend provider
  [default.resilience.locking.provider]
  backend = "redis"
  
    # The redis provider reuses a KVStore connection configuration.
    [default.resilience.locking.provider.kvstore]
    # The namespace and other wrappers will apply to the lock keys
    namespace = "locks"
      [default.resilience.locking.provider.kvstore.provider]
      backend = "redis"
      uri = "redis://localhost:6379/5"
```

---

## API Reference

::: nala.athomic.resilience.locking.decorator.distributed_lock

::: nala.athomic.resilience.locking.protocol.LockingProtocol

::: nala.athomic.resilience.locking.exceptions.LockAcquisitionError