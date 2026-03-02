# Base Service & Lifecycle

## Overview

The `BaseService` is a fundamental building block within the Athomic Layer. It provides a standardized protocol (`BaseServiceProtocol`) for all long-running or stateful components that have a defined lifecycle (e.g., a database connection manager, a message consumer, a background poller).

## Key Lifecycle Methods

-   `start()`: Initializes the service and its dependencies.
-   `stop()`: Gracefully shuts down the service and releases resources.
-   `wait_ready()`: An awaitable method that resolves only when the service is fully initialized and ready to be used.
-   `is_ready()`: A boolean property to check the current readiness state.

This consistent interface allows the **[Lifecycle Management](./lifecycle.md)** system to orchestrate the application's startup and shutdown sequences in a reliable and predictable order.