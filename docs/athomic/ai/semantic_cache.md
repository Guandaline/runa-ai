# Semantic Caching

## Overview

The Semantic Cache module provides an intelligent caching layer for Large Language Model (LLM) interactions. Unlike traditional exact-match caching (hash-based), Semantic Caching uses **Vector Similarity** to identify requests that are *semantically equivalent* even if phrased differently.

For example, "How much does it cost?" and "What is the price?" are distinct strings but have the same semantic intent. This module detects this similarity and serves the cached response, significantly reducing:
1.  **Latency**: Returning a cached JSON object is orders of magnitude faster than generating tokens.
2.  **Cost**: Reduces calls to expensive LLM providers (GPT-4, etc.).

---

## Architecture

The module implements a **Hybrid Cache Pattern** using two distinct data stores:

1.  **Vector Store (e.g., Qdrant)**:
    * Stores the **Embeddings** of the user prompts.
    * Used for the "Similarity Search" phase.
    * Enforces **Tenant Isolation** using metadata filters.
2.  **Key-Value Store (e.g., Redis)**:
    * Stores the actual heavy payload (**LLMResponse**).
    * Handles **TTL (Time-To-Live)** and automatic expiration of old cache entries.

### The Flow

1.  **Lookup**:
    * The user's prompt is converted into a vector embedding.
    * The system searches the Vector Store for the nearest neighbor within the current tenant's scope.
    * If a match is found with a score higher than the configured `score_threshold`, it is considered a **Hit**.
    * The system fetches the full response payload from the KV Store using the key stored in the vector's metadata.
2.  **Storage**:
    * Occurs asynchronously (background task) after a "Miss".
    * The prompt is embedded and upserted into the Vector Store.
    * The full `LLMResponse` is serialized and saved to the KV Store.

---

## Usage Example

The `SemanticCacheService` is typically used as a middleware or decorator around the `BaseLLM`.

```python
from nala.athomic.ai.semantic_cache.factory import SemanticCacheFactory
from nala.athomic.context import context_vars

async def generate_with_cache(user_prompt: str):
    # 1. Initialize the service
    # (In production, this is usually a singleton created at startup)
    cache_service = SemanticCacheFactory.create()
    
    # 2. Set context (Crucial for Tenant Isolation)
    context_vars.set_tenant_id("tenant-123")

    # 3. Try Lookup
    cached_response = await cache_service.lookup(user_prompt)
    
    if cached_response:
        print(f"Cache Hit! (Score: {cached_response.metadata['cache_score']})")
        return cached_response

    # 4. On Miss: Generate and Store
    print("Cache Miss. Calling LLM...")
    response = await llm.generate(user_prompt)
    
    # Store for future use (fire-and-forget recommended in production)
    await cache_service.store(user_prompt, response)
    
    return response
```

---

## Configuration

The semantic cache is configured under `[ai.semantic_cache]` in `settings.toml`.

```toml
[default.ai.semantic_cache]
# Master switch to enable/disable the cache logic
enabled = true

# Minimum similarity score (0.0 to 1.0) to consider a match.
# 0.95 is recommended for high precision.
score_threshold = 0.95

# Time-To-Live for cached entries in seconds (e.g., 24 hours).
ttl_seconds = 86400

# The name of the collection in the Vector Store.
collection_name = "semantic_cache_v1"

# --- Connection Bindings ---

# References a connection defined in [database.vector]
vector_store_connection_name = "default_qdrant"

# References a connection defined in [database.kvstore]
kv_store_connection_name = "default_redis"

# References a connection defined in [ai.connections] used for embedding the prompt
embedding_model_connection = "openai_text_embedding_3"
```

---

## API Reference

::: nala.athomic.ai.semantic_cache.service.SemanticCacheService

::: nala.athomic.ai.semantic_cache.protocol.SemanticCacheProtocol

::: nala.athomic.ai.semantic_cache.factory.SemanticCacheFactory

::: nala.athomic.config.schemas.ai.SemanticCacheSettings