# Lifecycle Management

## Overview

The `LifecycleManager` is the central orchestrator responsible for managing the startup and shutdown sequences of all registered `BaseService` instances in the application.

### How It Works

1.  **Registration**: Services are registered with the `LifecycleManager`, optionally declaring dependencies on other services.
2.  **Startup**: When `manager.start_all()` is called, it builds a dependency graph and starts the services in the correct topological order. It uses `asyncio.gather` to start independent services concurrently, optimizing startup time.
3.  **Readiness**: The manager waits for all services to become "ready" by calling their `wait_ready()` method. The application is only considered fully started after all essential services are ready.
4.  **Shutdown**: When `manager.stop_all()` is called, it shuts down all services in the reverse order of their startup, ensuring a graceful teardown.

This system guarantees that a service that depends on a database connection will only start *after* the database connection manager is ready, preventing race conditions and startup errors.

## API Reference
::: nala.athomic.lifecycle.manager.LifecycleManager
::: nala.athomic.lifecycle.registry.LifecycleRegistry