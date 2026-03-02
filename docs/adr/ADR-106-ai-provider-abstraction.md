# ADR-106: AI Provider Abstraction Strategy

* **Status:** Accepted
* **Date:** 2025-12-04

## Context

The application needs to integrate with multiple Generative AI providers (e.g., OpenAI, Google Vertex AI) for text generation and vector embeddings.
Directly coupling the domain logic to specific vendor SDKs (like `openai` or `google-cloud-aiplatform`) creates vendor lock-in, makes testing difficult, and complicates the configuration management when switching providers based on cost or availability.
Furthermore, different providers handle "Structured Output" (JSON extraction) differently, requiring a unified interface to ensure reliability across models.

## Decision

We decided to implement a **Protocol-based abstraction layer** with a **Registry pattern** for both LLMs and Embeddings.

### 1. Unified Protocols
We defined `LLMProviderProtocol` and `EmbeddingModelProtocol` to enforce a standard API contract.
* **LLM Protocol:** Enforces `generate_content` for unstructured text and `generate_structured` for strict Pydantic schema extraction.
* **Embedding Protocol:** Explicitly separates `embed_documents` (for storage) and `embed_query` (for retrieval) to support asymmetric embedding models (like Google Vertex/Gecko).

```python
class LLMProviderProtocol(Protocol):
    async def generate_content(self, prompt: str, ...) -> str: ...
    async def generate_structured(self, prompt: str, response_model: Type[T], ...) -> T: ...
```

### 2. Registry Pattern
We implemented `LLMProviderRegistry` and `EmbeddingRegistry`. These registries map simple backend strings (e.g., "openai", "vertex") to their concrete provider classes. This allows the application to select the implementation at runtime based on the `settings.toml` configuration.

### 3. Standardized Exception Hierarchy
All vendor-specific errors are caught within the provider implementation and re-raised as standardized Athomic exceptions. This ensures that upstream consumers do not need to handle `openai.RateLimitError` or `google.api_core.exceptions.ResourceExhausted` separately.
* `ProviderError`: Generic 5xx API errors.
* `AuthenticationError`: Invalid keys or permissions.
* `ContextWindowExceededError`: Token limit violations.

## Consequences

* **Positive:**
    * **Vendor Agnosticism:** Switching from GPT-4 to Gemini requires only a configuration change; no code changes are needed in the business logic.
    * **Structured Data Reliability:** The `generate_structured` method standardizes how JSON is extracted and validated against Pydantic models, abstracting the differences between OpenAI Tools and Vertex Function Calling.
    * **Resilience:** Unified error handling allows for generic retry policies and circuit breakers to work effectively across different providers.

* **Negative:**
    * **Feature Lag:** New, vendor-specific features (e.g., OpenAI Assistants API, specific caching parameters) are not immediately available via the generic protocol unless specific extensions are added.
    * **Abstraction Leakage:** Prompt engineering often varies by model family. A prompt optimized for GPT-4 might perform poorly on Gemini, requiring model-specific prompt management despite the code abstraction.

* **Neutral/Other:**
    * **Lazy Loading:** Dependencies for providers are imported locally within the registry to avoid installing heavy SDKs (like `vertexai`) if they are not used in a particular environment.