# Key-Value Stores

## Overview

The Key-Value (KV) Store module provides a powerful and extensible abstraction layer for interacting with key-value data stores like Redis. It is a fundamental building block used by many other Athomic modules, including:

-   **Caching**: For storing the results of expensive operations.
-   **Rate Limiting**: For tracking request counts.
-   **Feature Flags**: For fetching flag configurations.
-   **Distributed Locking**: For managing lock states.
-   **Sagas & Schedulers**: For persisting state and scheduled tasks.

The architecture is designed to be highly flexible, featuring a protocol-based design, multiple backend providers, and a powerful wrapper system that allows for adding cross-cutting functionality declaratively.

---

## Core Concepts

### `KVStoreProtocol`

This is the contract that all KV store providers must implement. It defines a rich set of asynchronous operations, including not only basic CRUD (`get`, `set`, `delete`, `exists`) but also advanced commands for **sorted sets** (`zadd`, `zrem`, `zpopbyscore`), which are critical for implementing components like the task scheduler.

### `KVStoreFactory`

This is the main entry point for creating a KV store client. The factory is responsible for:
1.  Reading the configuration for a named connection.
2.  Instantiating the correct base provider (e.g., `RedisKVClient`) using a registry.
3.  **Applying a chain of wrappers** to the base provider, adding functionality like multi-tenancy and default TTLs.

### Wrapper (Decorator) Pattern

A key architectural feature of the KV Store module is its use of the Decorator pattern. You can "wrap" a base client with additional functionality defined in your configuration. This makes the system extremely flexible. For example, you can add multi-tenant key resolution to any KV store (Redis, in-memory, or a future DynamoDB provider) just by adding a wrapper to the configuration.

---

## Available Providers

-   **`RedisKVClient`**: The primary, production-ready provider for **Redis**. It uses the high-performance `redis-py` async client and supports the full `KVStoreProtocol`, including atomic sorted set operations implemented with Lua scripting for maximum safety.
-   **`LocalKVClient`**: A simple, in-memory provider that simulates a KV store using Python dictionaries. It is perfect for fast, dependency-free unit and integration testing.

## Available Wrappers

-   **`KeyResolvingKVClient`**: This wrapper automatically prepends contextual prefixes to all keys before they hit the database. It uses the `ContextKeyGenerator` to include the `namespace`, `tenant_id`, and `user_id` (if configured), making multi-tenancy transparent.
-   **`DefaultTTLKvClient`**: This wrapper automatically applies a default Time-To-Live (TTL) to all `set` operations if one is not explicitly provided in the method call. This is useful for ensuring that cache keys, for example, always expire.

---

## Configuration

The true power of this module is visible in its configuration. You define a base provider and then apply a list of wrappers to it.

```toml
# In settings.toml, under [default.database.kvstore]

[default.database.kvstore.default_redis]
enabled = true
# The namespace is used by the KeyResolvingKVClient wrapper
namespace = "cache"

  # 1. Define the base provider (e.g., Redis)
  [default.database.kvstore.default_redis.provider]
  backend = "redis"
  uri = "redis://localhost:6379/0"

  # 2. Define an ordered list of wrappers to apply
  [[default.database.kvstore.default_redis.wrappers]]
  name = "default_ttl" # This must match a name in the KVStoreWrapperRegistry
  enabled = true
    # Custom settings for this wrapper instance
    [default.database.kvstore.default_redis.wrappers.config]
    default_ttl_seconds = 3600 # 1 hour

  [[default.database.kvstore.default_redis.wrappers]]
  name = "key_resolver"
  enabled = true
    # The 'namespace' from the top level will be used by this wrapper
    [default.database.kvstore.default_redis.wrappers.config]
    # No extra config needed here, it uses the parent's namespace
```

In this example, when a `set("my-key", "value")` call is made, the final key in Redis will look something like `nala:tenant-123:cache:my-key`, and it will have a default TTL of 1 hour.

---

## API Reference

::: nala.athomic.database.kvstore.protocol.KVStoreProtocol

::: nala.athomic.database.kvstore.factory.KVStoreFactory

::: nala.athomic.database.kvstore.providers.redis.client.RedisKVClient

::: nala.athomic.database.kvstore.wrappers.key_resolver_kv_client.KeyResolvingKVClient

::: nala.athomic.database.kvstore.wrappers.default_ttl_kv_client.DefaultTTLKvClient