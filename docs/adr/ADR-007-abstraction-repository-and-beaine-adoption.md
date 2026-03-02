# ADR-007: Repository Abstraction and Beanie ODM for MongoDB

* **Status:** Accepted (Implemented)
* **Date:** 2025-04-13 (Placeholder)

## Context

* **Problem:** Applications need to interact with data persistence layers (databases). Directly using database driver code (e.g., `motor` for async MongoDB [source: 5]) or even a specific Object-Document Mapper (ODM) / Object-Relational Mapper (ORM) (like `Beanie` [source: 5], SQLAlchemy) within business logic (services) or API handlers creates tight coupling between the application logic and the specific database technology and its access patterns. This coupling makes it difficult to:
    * Switch database technologies in the future (e.g., migrating from MongoDB to PostgreSQL) without extensive refactoring.
    * Unit test business logic in isolation without needing a live database connection or complex mocking of the database driver/ODM.
    * Maintain consistency in how data is accessed and manipulated across different parts of the application.
    * Evolve the data model and access logic independently of the business rules.
* **Goal:** Abstract the data access logic behind a stable, consistent interface using the Repository pattern. This aims to decouple the business logic from the specific database implementation, thereby improving testability, maintainability, and the potential for future database migrations. Additionally, leverage an asynchronous ODM for MongoDB to simplify database interactions, provide schema validation close to the database, and integrate well with the FastAPI/asyncio ecosystem.
* **Alternatives Considered:**
    * **Direct Driver/ODM Usage:** Using `motor` or `Beanie` directly within service classes or FastAPI route functions. *Drawback:* Leads to high coupling, poor testability, and mixes data access concerns with business/API logic.
    * **Generic ORM/ODM Only (e.g., SQLAlchemy Core, Pymongo):** Using lower-level database interaction tools. *Drawback:* Requires significantly more boilerplate code for common CRUD (Create, Read, Update, Delete) operations compared to a higher-level ODM like Beanie. Type safety for data models might be less integrated.
    * **Data Access Objects (DAOs):** A pattern similar to Repositories, but sometimes considered more focused on simple CRUD operations per table/collection. *Decision:* The Repository pattern felt more aligned with encapsulating operations related to a whole business entity/aggregate, potentially including more complex queries beyond simple CRUD.
    * **Other Async ODMs for MongoDB:** Evaluating alternatives to Beanie (e.g., `MongoEngine` - though async support might be less mature, `ODMantic` - another Pydantic-based option). *Decision:* Beanie was chosen due to its strong integration with Pydantic and FastAPI, its active development, and its focus on async. [source: 5]

## Decision

* Implement the **Repository Pattern** as the standard way to abstract data persistence logic within `athomic`.
* Define a generic **`IRepository` Protocol** [source: 1000] using `typing.Protocol` to specify the common contract for data access, including methods like `get_by_id`, `save`, `delete`, `find`, `find_one`.
* Define **specific repository interfaces** (e.g., `IUserRepository` [source: 1006]) that inherit from `IRepository` for each core domain entity (like User). These specific interfaces can include methods relevant only to that entity (e.g., `get_by_email`).
* Utilize the **`Beanie` ODM** [source: 5] as the chosen tool for interacting with MongoDB. Beanie leverages `motor` for asynchronous operations and `Pydantic` for defining document models (`beanie.Document`) [source: 1030, 1142], providing data validation and a convenient API.
* Implement **concrete repository classes** specifically for the MongoDB backend using Beanie. This includes:
    * A generic `MongoBeanieRepository` [source: 1031] class that implements the `IRepository` protocol using Beanie's methods.
    * Specific repository classes (e.g., `MongoUserRepository` [source: 1035]) that inherit from the generic Beanie repository *and* the specific domain interface (e.g., `IUserRepository`), implementing any additional required methods using Beanie queries.
* Utilize the **Factory Pattern** via the `get_repository` function [source: 1009]. This function:
    1. Reads the configured database backend from settings (`settings.database.backend` [source: 846, 1010]).
    2. Uses a mapping (`_REPOSITORY_IMPLEMENTATIONS` [source: 1007]) to look up the appropriate concrete repository class based on the requested *interface* type and the configured backend.
    3. Instantiates and returns the concrete repository class (often cached via `@lru_cache` for efficiency).
* Centralize the MongoDB connection and Beanie initialization logic in **`nala.athomic.db.mongo.beanie_init.py`** [source: 1036]. This initialization (`init_database_connection` [source: 1038]) is designed to be called once during the application startup sequence (e.g., within the FastAPI `lifespan` manager [source: 1151]).

## Consequences

* **Positive:**
    * **Decoupling:** Business logic components (services) depend only on the repository interfaces, making them theoretically agnostic to the underlying database technology (MongoDB/Beanie in this implementation).
    * **Improved Testability:** Business logic can be easily unit-tested by injecting mock repository objects that conform to the defined interfaces, eliminating the need for a live database in unit tests.
    * **Centralized Data Access Logic:** All database interaction logic for a given entity is concentrated within its repository implementation, improving code organization, maintainability, and consistency.
    * **Developer Productivity (for MongoDB):** Beanie significantly simplifies common MongoDB operations (CRUD, indexing, potentially data migrations) and integrates seamlessly with Pydantic for data validation at the ODM level. [source: 1031-1034]
    * **Extensibility:** Adding support for a different database technology (e.g., PostgreSQL with SQLAlchemy) would primarily involve creating new repository classes implementing the existing interfaces and updating the factory mapping, with minimal changes to the business logic layer. [source: 1008]
* **Negative:**
    * **Layer of Indirection:** Introduces an extra layer of abstraction (interfaces, factory) compared to using the ODM or database driver directly.
    * **Boilerplate Code:** Requires defining interface files and implementation classes for each repository, adding some boilerplate.
    * **Potential for Leaky Abstraction:** Very complex or database-specific queries might be awkward or inefficient to express through the generic repository interface. This could necessitate adding specialized methods to interfaces or accepting that some database-specific constructs (like Beanie's query syntax) might leak into the criteria passed to methods like `find` or `find_one` [source: 1034].
    * **Dependency on Beanie (for Mongo):** While the business logic is decoupled from MongoDB *in principle*, the current concrete implementation is tightly coupled to the Beanie ODM. Migrating *away* from Beanie, even while still using MongoDB, would require rewriting the repository implementations.
* **Neutral/Other:**
    * The current pattern assumes a single primary database is configured via `settings.database` [source: 846]. Supporting connections to multiple databases simultaneously (of the same or different types) would require extending the configuration schema and the repository factory logic.
    * The correct functioning relies on the successful initialization of the database connection and Beanie ODM during application startup (`init_database_connection` [source: 1038]). Failures during startup need to be handled appropriately.