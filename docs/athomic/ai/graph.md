# AI Knowledge Graph Module (`nala.athomic.ai.graph`)

This module provides Semantic Knowledge Graph capabilities to the architecture, enabling structured entity storage and relational retrieval (GraphRAG). It bridges the gap between unstructured text and structured knowledge using LLM-based extraction and Graph Database persistence.

## Architecture

The module adheres to the Clean Architecture principles using Protocols for dependency inversion:

* **Service Layer (`GraphService`):** The main orchestrator that manages the lifecycle, observability (metrics/tracing), and delegates storage operations.
* **Storage Layer (`GraphStoreProtocol`):** A backend-agnostic interface for graph databases.
    * **Memory:** `NetworkX` implementation for testing and ephemeral graphs.
    * **Cypher:** `Neo4j` implementation for production, using optimized Cypher queries.
* **Extraction Layer (`GraphExtractorProtocol`):** Components that convert raw text into `GraphNode` and `GraphEdge` objects using LLMs.
* **Query Layer (`GraphQueryEngine`):** Analyzes user questions to identify "Anchor Nodes" for hybrid retrieval (GraphRAG).

## Configuration

Configuration is managed via `GraphAISettings`. Enable the module in your `config.toml` or environment variables:

```toml
[ai.graph]
ENABLED = true
BACKEND = "neo4j"  # Options: "memory", "neo4j"
CONNECTION_NAME = "default_graph"
STRICT_SCHEMA = true
EXTRACTION_MODEL_CONNECTION = "gpt-4-turbo"
```

## Usage

### 1. Initialization

The service is typically instantiated via the dependency injection container, which uses the `GraphStoreFactory` to load the correct backend.

```python
from nala.athomic.ai.graph.service import GraphService
from nala.athomic.config import get_settings

# Manual initialization (if not using DI)
settings = get_settings().ai.graph
service = GraphService(settings=settings)

# Connects to the configured backend (Memory or Neo4j)
await service.connect()
```

### 2. Manual Knowledge Ingestion

You can ingest explicit knowledge using domain objects (`GraphNode`, `GraphEdge`).

```python
from nala.athomic.ai.schemas.graph import GraphNode, GraphEdge

# 1. Define Nodes
node_user = GraphNode(
    id="u123",
    label="Person",
    name="Alice",
    properties={"role": "Engineer"}
)

node_tech = GraphNode(
    id="t99",
    label="Technology",
    name="Python",
    properties={"version": "3.12"}
)

# 2. Define Relationship
edge = GraphEdge(
    source_id="u123",
    target_id="t99",
    relation="KNOWS",
    weight=0.9,
    properties={"proficiency": "expert"}
)

# 3. Persist to Graph
await service.add_knowledge(nodes=[node_user, node_tech], edges=[edge])
```

### 3. LLM Extraction

Extracts entities and relationships from unstructured text using the `LLMGraphExtractor`.

```python
from nala.athomic.ai.graph.extractors.llm import LLMGraphExtractor

extractor = LLMGraphExtractor(
    llm_provider=llm_provider,
    prompt_source=prompt_source,
    prompt_renderer=prompt_renderer
)

text = "Alice is an expert in Python and works at Acme Corp."
nodes, edges = await extractor.extract(text)

# Persist extracted knowledge
await service.add_knowledge(nodes, edges)
```

### 4. Context Retrieval (GraphRAG)

Retrieves the semantic neighborhood of an entity to enrich LLM prompts.

```python
# 1. Find the entry point entity
results = await service.search_entities(
    label="Person",
    properties={"name": "Alice"}
)

if results:
    alice_id = results[0].id
    
    # 2. Get 1-hop context
    context = await service.get_context(node_id=alice_id, depth=1)
    
    for edge in context.edges:
        # e.g., "Alice -[KNOWS]-> Python"
        print(f"Edge: {edge.source_id} -[{edge.relation}]-> {edge.target_id}")
```

### 5. Query Understanding (GraphQueryEngine)

Extracts entities from a user question to serve as entry points (anchors) for the graph search.

```python
from nala.athomic.ai.graph.engine import GraphQueryEngine

# 1. Initialize Engine (wraps extractor logic)
query_engine = GraphQueryEngine(graph_service=service)

# 2. Extract Anchors
# Finds nodes in the question that likely exist in the graph
anchors = await query_engine.extract_anchors("Who founded the company that bought Pixar?")
print(anchors) 
# Output: ['Pixar']
```

## Observability

The module automatically records Prometheus metrics and OpenTelemetry traces:
* `graph_ai_operations_total`: Counter for operation throughput/status.
* `graph_ai_operation_duration_seconds`: Histogram for latency.