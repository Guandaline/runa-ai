# Semantic Memory Service

## Overview

The `SemanticMemoryService` acts as an orchestration facade for **Retrieval-Augmented Generation (RAG)**. It combines the capabilities of [Embeddings](./embeddings.md) and [Vector Stores](../database/vector.md) to provide a high-level API for storing and recalling semantic information.

Instead of manually wiring an embedding model to a vector database in every application service, developers use this unified service to "add" memories (text) and "recall" them (search).

---

## Features

-   **Orchestration**: Automatically handles the flow: `Text -> Embedding -> Vector Record -> DB Upsert`.
-   **Asymmetric Support**: Correctly uses `embed_documents` for storage and `embed_query` for retrieval.
-   **Standardized Metadata**: Automatically manages creation timestamps and metadata persistence.
-   **Tracing**: Provides a holistic trace span (`memory.add`, `memory.recall`) encompassing the entire RAG operation.

---

## Usage

```python
from nala.athomic.ai.memory.factory import SemanticMemoryFactory

async def remember_user_preference(user_id: str, preference: str):
    # 1. Initialize the service (automatically wires DB and AI)
    memory_service = SemanticMemoryFactory.create(collection_name="user_context")
    
    # 2. Add a memory with metadata
    await memory_service.add(
        content=preference,
        metadata={"user_id": user_id, "type": "preference"}
    )

async def get_relevant_context(user_id: str, question: str):
    memory_service = SemanticMemoryFactory.create(collection_name="user_context")

    # 3. Recall relevant memories
    # The 'filters' argument is passed down to the Vector Store
    results = await memory_service.recall(
        query=question,
        limit=3,
        filters={"user_id": user_id}
    )
    
    return [res.memory.content for res in results]
```

---

## API Reference

::: nala.athomic.ai.memory.service.SemanticMemoryService

::: nala.athomic.ai.memory.types.Memory

::: nala.athomic.ai.memory.types.MemorySearchResult