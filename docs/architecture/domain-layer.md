# The Domain Layer

The Domain Layer is the core of the application. It contains the business logic, rules, and state that are unique to your specific problem domain. This layer is designed to be completely independent of any infrastructure concerns—it knows nothing about databases, web frameworks, or message brokers.

## Key Concepts

-   **Entities & Aggregates**: These are the primary objects that model your domain. An Aggregate is a cluster of associated objects that we treat as a single unit for data changes.
-   **Value Objects**: Objects that represent a descriptive aspect of the domain with no conceptual identity.
-   **Domain Events**: Objects that represent something that happened in the domain. They are often used to communicate changes between different parts of the application without direct coupling.
-   **Repositories**: Interfaces defined in the Domain Layer that specify the contract for data persistence (e.g., `save(user)`, `find_by_id(user_id)`). The *implementation* of these interfaces lives in the Infrastructure Layer.

By keeping the Domain Layer pure, you ensure that your most critical business logic is easy to test, maintain, and evolve independently of technology choices.