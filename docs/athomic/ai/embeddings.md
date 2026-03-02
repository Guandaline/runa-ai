# Embeddings

## Overview

The Embeddings module provides a unified interface for text-to-vector transformation services. It is the engine powering the [Vector Store](../database/vector.md) and [Document Ingestion](./documents.md) modules.

With the introduction of the `EmbeddingManager`, this module now supports robust lifecycle management and connection pooling, mirroring the architecture of the LLM module.

### Key Features

-   **Unified Management**: The `EmbeddingManager` handles the initialization and reuse of embedding providers.
-   **Shared Configuration**: Reuses the `[ai.connections]` configuration group, allowing you to use the same provider settings (e.g., OpenAI API Key) for both Chat and Embeddings.
-   **Asymmetric Support**: Supports models that differentiate between query and document embeddings (e.g., Vertex AI Gecko).

---

## Usage Example

```python
from nala.athomic.ai.embeddings import embedding_manager

async def get_vector(text: str):
    # 1. Get a client by name (defined in settings)
    # The manager handles initialization/caching.
    model = embedding_manager.get_client("openai_default")
    
    # 2. Generate vector
    vector = await model.embed_query(text)
    return vector
```

---

## Configuration

Embeddings use the shared `[ai.connections]` pool. You specify which connection to use as default for embeddings in the root `[ai]` section.

```toml
[default.ai]
enabled = true
# Default connection for Chat/Generation
default_connection_name = "gpt4"
# Default connection specifically for Embeddings
default_embeddings_connection_name = "text_embedding_3"

  # Define the connection once
  [default.ai.connections.connections.text_embedding_3]
  backend = "openai"
  default_model = "text-embedding-3-small"
  
    [default.ai.connections.connections.text_embedding_3.provider]
    api_key = "..."
```

---

## API Reference

::: nala.athomic.ai.embeddings.manager.EmbeddingManager

::: nala.athomic.ai.embeddings.factory.EmbeddingFactory

::: nala.athomic.ai.embeddings.protocol.EmbeddingModelProtocol