# Document Ingestion (RAG ETL)

## Overview

The Document Ingestion module provides a high-level orchestration service for transforming unstructured data (PDFs, Text files) into semantic vectors persisted in a Vector Store. It implements a complete **Extract-Transform-Load (ETL)** pipeline designed for Retrieval-Augmented Generation (RAG).

### Key Features

-   **Modular Loaders**: Support for multiple file formats (`.txt`, `.pdf`, `.md`) via a plugin-like registry.
-   **Flexible Splitting Strategies**: Supports multiple chunking algorithms via the **Strategy Pattern**:
    -   **Recursive Character**: Preserves semantic structure (paragraphs, headers).
    -   **Token Based**: Optimizes chunks for LLM context windows (using `tiktoken`).
-   **Managed Pipeline**: Coordinates loading, splitting, embedding, and upserting in a single method call.
-   **Observability**: Metrics tracks pages loaded, chunks created, and processing latency.

---

## How It Works

1.  **Extract (Load)**: The service detects the file extension and selects the appropriate `DocumentLoader` (e.g., `PDFLoader` using `pypdf`) to extract raw text and metadata (page numbers, filenames).
2.  **Transform (Split)**: The raw text is passed to the configured `TextSplitter` strategy (instantiated via `SplitterFactory`). This divides the text into chunks based on the configured strategy (e.g., token count or character separators).
3.  **Load (Persist)**: The chunks are sent to the `SemanticMemoryService`, which generates embeddings and upserts them into the configured `VectorStore`.

---

## Usage Example

```python
from nala.athomic.ai.documents import DocumentIngestionFactory

async def ingest_knowledge_base(file_path: str):
    # 1. Get the pre-configured service
    # The factory will load the correct splitter strategy from settings
    ingestion_service = DocumentIngestionFactory.create_default()
    await ingestion_service.connect()

    # 2. Ingest the file
    # Handles loading, splitting, embedding, and storage automatically.
    memory_ids = await ingestion_service.ingest(
        source=file_path,
        filename="company_policy.pdf",
        metadata={"category": "hr_policy", "version": "1.0"}
    )
    
    print(f"Successfully created {len(memory_ids)} vector records.")
```

---

## Configuration

Ingestion parameters are configured under `[ai.documents]` in `settings.toml`. The module uses a **Polymorphic Configuration** for the splitter, allowing you to choose between strategies.

### Strategy: Recursive Character (Default)

Best for general text where preserving paragraph structure is important.

```toml
[default.ai.documents]
enabled = true

  [default.ai.documents.splitter]
  strategy = "recursive_character"
  chunk_size = 1000       # Target characters per chunk
  chunk_overlap = 200     # Overlap to maintain context
  separators = ["\n\n", "\n", " ", ""]
  keep_separator = true
  is_separator_regex = false
```

### Strategy: Token Splitter (LLM Optimized)

Best for ensuring chunks fit exactly into model context windows (e.g., GPT-4).

```toml
[default.ai.documents]
enabled = true

  [default.ai.documents.splitter]
  strategy = "token"
  chunk_size = 512        # Target tokens (not characters)
  chunk_overlap = 50
  encoding_name = "cl100k_base" # Encoding for GPT-3.5/4
  decode_unicode_errors = "ignore"
```

---

## API Reference

::: nala.athomic.ai.documents.service.DocumentIngestionService

::: nala.athomic.ai.documents.splitters.protocol.TextSplitterProtocol

::: nala.athomic.config.schemas.ai.documents.splitting_settings.SplitterConfigTypes