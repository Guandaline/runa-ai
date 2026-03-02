# Retrieval-Augmented Generation (RAG)

## Overview

The **RAG Module** (`nala.athomic.ai.rag`) orchestrates the retrieval of semantic knowledge and its synthesis into generative responses. It bridges the gap between your static knowledge base and the dynamic reasoning capabilities of Large Language Models (LLMs). It utilizes a **Stream-First Architecture** and supports **Advanced RAG** patterns to improve retrieval accuracy.

### Key Features

-   **True Streaming**: Delivers retrieval sources ("citations") immediately in the first chunk, followed by the answer.
-   **Hybrid GraphRAG**: Combines vector similarity search with knowledge graph traversal to answer complex relational questions.
-   **Polymorphic Strategy Pattern**: Decouples retrieval logic from generation logic using a dynamic `RetrievalFactory` and `RetrievalCreatorRegistry`, supporting seamless switching between `vector`, `graph`, and `hybrid` backends.
-   **Pluggable Fusion Algorithms**: Includes a `FusionRegistry` to synthesize hybrid results using dynamic algorithms like Reciprocal Rank Fusion (RRF) and Weighted Sum.
-   **Safe XML Prompt Injection**: The `StuffGenerationStrategy` automatically sanitizes and escapes retrieved context into isolated `<doc>` tags to prevent prompt injection attacks and context corruption.
-   **Advanced Retrieval**: Supports **HyDE** (Hypothetical Document Embeddings) and **Cross-Encoder Re-ranking** to maximize context relevance.
-   **Metadata Filtering**: Allows refining vector search results using structured data (e.g., date, category).
-   **Full Observability**: Granular metrics for every stage: Expansion -> Retrieval -> Fusion -> Re-ranking -> Generation.

---

## Architecture



The Advanced RAG pipeline executes in distinct phases, heavily utilizing the **Dual-Path Retrieval** strategy and concurrent processing:

1.  **Query Understanding & Expansion**:
    * **HyDE**: Generates a "hypothetical answer" to optimize vector search.
    * **Graph Extraction**: Extracts named entities (Anchor Nodes) from the query to traverse the Knowledge Graph.

2.  **Dual-Path Retrieval Phase**:
    * **Path A (Vector)**: Queries the **[Semantic Memory](../ai/memory.md)** for unstructured text chunks based on embedding similarity.
    * **Path B (Graph)**: Uses the **[Graph Module](../ai/graph.md)** to fetch the immediate structural neighborhood (context) of the extracted entities.

3.  **Context Fusion Phase**:
    * Results from both paths are executed concurrently (via `asyncio.gather`) and merged using dynamic algorithms (e.g., Reciprocal Rank Fusion or Weighted Sum) managed by the `FusionRegistry`.
    * **Token Budgeting**: The system intelligently allocates context window space to ensure a balanced prompt across distinct sources.

4.  **Re-ranking Phase**:
    * A high-precision **Cross-Encoder model** evaluates the relevance of the fused documents against the original query.
    * *Optimization:* The synchronous model prediction is offloaded to a thread pool executor to prevent blocking the asynchronous event loop during high concurrency.
    * Documents are re-scored and sorted. Only the top results are kept.

5.  **Context Optimization Phase**:
    * The pipeline interacts with the **[Context Module](../ai/context.md)** to calculate the exact **Token Budget**.
    * It iterates through the re-ranked documents and **truncates** or drops chunks that would cause a Context Window Overflow.

6.  **Generation Phase**:
    * The highly relevant (and optimized) context is sanitized, escaped, and injected into `<doc>` XML tags within the prompt template (`rag/qa`).
    * The LLM generates the final answer, which is streamed securely to the client.

---

## Usage Example

### Basic Streaming Request

```python
from nala.athomic.ai.rag.factory import RAGFactory
from nala.athomic.ai.schemas.rag import RAGRequest

async def ask_knowledge_base(question: str):
    # 1. Initialize Service
    rag_service = RAGFactory.create()
    await rag_service.connect()

    # 2. Prepare the Request
    request = RAGRequest(query=question)
    
    # 3. Iterate over response stream
    async for chunk in rag_service.stream_response(request):
        if chunk.sources:
            print(f"\n[Sources Found]: {[s.document_id for s in chunk.sources]}")
        
        if chunk.content_delta:
            print(chunk.content_delta, end="", flush=True)
```

---

## Advanced Usage

### Metadata Filtering

To prevent the model from using outdated or irrelevant information, you can apply structured filters. These filters are passed down to the Vector Database.

```python
# Search for "Revenue", but ONLY in documents tagged as 'finance' from '2024'
request = RAGRequest(
    query="What was the Q3 revenue?",
    limit=10,
    filters={
        "category": "finance",
        "year": 2024,
        "status": "published"
    }
)

response = await rag_service.generate_response(request)
```

### Controlling Advanced Features

You can enable/disable HyDE or Re-ranking globally via configuration (see below), or you can control specific parameters per request if the strategy allows.

---

## Configuration

RAG is configured under `[ai.rag]` in `settings.toml`. The architecture relies heavily on polymorphic configuration to resolve dynamic retrieval backends.

```toml
[default.ai.rag]
enabled = true
generation_strategy = "stuff"
default_prompt_template = "rag/qa"

# --- Polymorphic Retrieval Configuration ---
[default.ai.rag.retrieval]
backend = "hybrid"

[default.ai.rag.retrieval.provider]
backend = "hybrid"
fusion_algorithm = "rrf" # or "weighted"
vector_weight = 0.7
graph_weight = 0.3

# Nested Vector Settings
[default.ai.rag.retrieval.provider.vector]
backend = "vector"
top_k = 10

# Nested Graph Settings
[default.ai.rag.retrieval.provider.graph]
backend = "graph"
max_hops = 2
max_results = 20

# --- Advanced RAG: Query Expansion ---
[default.ai.rag.hyde]
enabled = true
prompt_template = "rag/hyde/v1"

# --- Advanced RAG: Re-ranking ---
[default.ai.rag.rerank]
enabled = true
# HuggingFace Cross-Encoder model
model_name = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
top_k = 5
score_threshold = 0.5
```

---

## Quality Assurance

When testing Advanced RAG, it is crucial to validate that re-ranking and fusion are actually improving results.

```python
# Example: Inspecting Re-ranking scores in tests
response = await rag_service.generate_response(request)

for source in response.sources:
    # The Cross-Encoder score is attached to metadata
    print(f"Doc: {source.document_id}, Score: {source.metadata.get('rerank_score')}")
```

---

## API Reference

::: nala.athomic.ai.rag.service.RAGService

::: nala.athomic.ai.schemas.rag.RAGRequest

::: nala.athomic.ai.rag.retrieval.factory.RetrievalFactory

::: nala.athomic.ai.rag.retrieval.strategies.hybrid.strategy.HybridRetrievalStrategy

::: nala.athomic.ai.rag.retrieval.strategies.hybrid.fusion.registry.FusionRegistry

::: nala.athomic.ai.rag.query_expansion.hyde_generator.HyDEGenerator

::: nala.athomic.ai.rag.rerank.strategies.cross_encoder.CrossEncoderReRanker