# ADR-109: Decoupled Prompt Management System

* **Status:** Accepted
* **Date:** 2025-12-08

## Context

The application requires a robust mechanism to manage the text prompts sent to Large Language Models (LLMs). 

Previously, prompts might have been hardcoded strings or managed in an ad-hoc manner. This approach presented several issues:
1.  **Lack of Versioning:** Modifying a prompt for testing could break production flows.
2.  **Tight Coupling:** Logic for reading files and formatting text was mixed with business logic.
3.  **Limited Logic:** Simple f-strings do not support complex conditions (e.g., "if user has history, include summary") required for advanced Agentic patterns.
4.  **Testing Difficulty:** Hard to mock file reads or complex template logic in unit tests.

We needed a system that separates the *storage* of prompts (File, DB) from the *rendering* of prompts (Jinja2, f-string) and orchestrates them via a unified Service.

## Decision

We have decided to implement a **Decoupled Prompt Management System** based on a layered architecture comprising Infrastructure (IO), Logic (Render), and Service layers.

### 1. Architectural Components

* **IO Layer (Loaders):** Responsible solely for retrieving the prompt definition (metadata + raw template) from a storage backend.
    * We defined a `PromptLoaderProtocol` to enforce consistency.
    * The initial implementation is `FileSystemPromptLoader`, which reads versioned YAML files from a directory structure (e.g., `prompts/sentiment/v1.0.0.yaml`).
    * It implements **Semantic Versioning Resolution**: If no version is requested, the loader automatically resolves the highest semantic version (e.g., `v1.10.0` > `v1.9.0`).

* **Render Layer (Engines):** Responsible solely for interpolating variables into the raw template string.
    * We defined a `PromptRendererProtocol`.
    * The chosen default engine is **Jinja2** (`JinjaPromptRenderer`). It allows for loops, conditionals, and filters within prompts.
    * We enforce `StrictUndefined`, meaning the system throws a `RenderError` immediately if a required variable is missing, preventing "hallucinated" empty values sent to the LLM.

* **Service Layer (Orchestrator):** The `PromptService` acts as a Facade.
    * It initializes the specific Loader and Renderer via Factories based on configuration.
    * It exposes a clean API: `render(name, variables)`.

### 2. Configuration & Factories

* We implemented the **Abstract Factory Pattern**. `PromptLoaderFactory` and `PromptRendererFactory` instantiate the correct classes based on `settings.backend` (e.g., "filesystem") and `settings.renderer` (e.g., "jinja2").
* **Simplification:** We explicitly decided **not** to use `ConnectionGroupSettings` for this module initially. The `PromptService` will operate as a single-tenant/single-connection service to reduce complexity. The configuration is a direct `PromptSettings` object.

### 3. Data Structure

* We utilize **Pydantic** models (`PromptTemplate`) to strictly validate the schema of loaded prompts (ensuring fields like `input_variables` and `template` exist) before any processing occurs.

## Consequences

### Positive
* **High Extensibility:** We can switch from FileSystem to MongoDB or Redis storage in the future by simply adding a new Loader class and changing one line in `settings.toml`. The Service code remains untouched.
* **Robustness:** The Jinja2 integration with strict validation ensures that incomplete data contexts are caught at the application layer, not at the API level of the LLM provider.
* **Safe Experimentation:** The versioning system allows developers to deploy `v2.0.0` of a prompt alongside `v1.0.0`, enabling A/B testing or Canary deployments by simply passing a version string to the service.
* **Testability:** The modular design allows unit testing the Renderer (logic) separately from the Loader (I/O), and integration testing the Service with mocked components.

### Negative
* **Filesystem Latency:** The current `FileSystemPromptLoader` reads from the disk on every request (unless the OS caches it). High-throughput scenarios might require implementing an in-memory caching decorator over the Loader.
* **Complexity:** The architecture introduces more boilerplate (factories, registries, protocols) compared to a simple function that reads a file.
* **File Management:** Developers must adhere to a strict directory and naming convention (`prompt_name/vX.Y.Z.yaml`) for the loader to function correctly.

### Neutral
* **Jinja2 Overhead:** While powerful, Jinja2 is slower than Python f-strings. Given the latency of LLM calls (seconds), the rendering time (microseconds) is negligible, but it is a dependency addition.