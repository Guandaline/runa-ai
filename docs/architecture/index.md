# Architecture Overview

The `athomic` follows a clean, layered architecture designed for separation of concerns, testability, and scalability. It is heavily inspired by principles from Domain-Driven Design (DDD) and Clean Architecture.

The main layers are:

-   **Domain Layer**: Contains the core business logic, entities, and rules. It is the heart of your application and has no dependencies on other layers.
-   **Application Layer**: Orchestrates the domain logic. It contains use cases and application services that handle requests from the outside world.
-   **Infrastructure Layer**: Implements external concerns like databases, message brokers, and third-party API clients.
-   **Athomic Layer**: A cross-cutting "engine" that provides foundational capabilities like caching, resilience, and observability to all other layers.