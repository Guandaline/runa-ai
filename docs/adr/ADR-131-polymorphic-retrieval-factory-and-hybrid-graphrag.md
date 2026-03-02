# ADR-131: Polymorphic Retrieval Factory and Hybrid GraphRAG Orchestration

* **Status:** Accepted
* **Date:** 2026-02-19

## Context

Nala's RAG system required an evolution from simple semantic vector search to a more advanced "Hybrid GraphRAG" engine. The goal was to combine the semantic precision of vector similarity with the deterministic structure of Knowledge Graphs to answer complex, relationship-based questions. 

Previously, the `RAGService` relied on a static or tightly coupled initialization of retrieval strategies. With the introduction of multiple standalone strategies (Vector, Graph) and the need to combine them (Hybrid), the monolithic approach to dependency injection and configuration parsing became a bottleneck. We needed a scalable architectural pattern to dynamically resolve, configure, and orchestrate these disparate retrieval mechanisms without bloating the core RAG service.

## Decision

We implemented a **Polymorphic Retrieval Strategy Pattern** supported by a dedicated Creator Registry and a parallel Hybrid Orchestrator. 

1. **Dynamic Factory and Registry:** We introduced a `RetrievalFactory` that abstracts the resolution of retrieval strategies. It relies on a `strategy_creator_registry` (managing `RetrievalCreator` instances) to dynamically instantiate the correct strategy at runtime. 
2. **Polymorphic Configuration:** The RAG settings were refactored to use a polymorphic `provider` block. Strategy-specific configurations are now resolved safely via a `backend` discriminator (e.g., `vector`, `graph`, `hybrid`).
3. **Hybrid Orchestrator (Parallel Execution):** We created a `HybridRetrievalStrategy` that acts as a composite. It executes the underlying Vector and Graph retrieval paths concurrently using `asyncio.gather`.
4. **Pluggable Fusion Algorithms:** The results from parallel paths are synthesized using algorithms managed by a `FusionRegistry`, with out-of-the-box support for Reciprocal Rank Fusion (RRF) and Weighted Sum.

## Consequences

* **Positive:**
    * **High Extensibility:** New retrieval backends (e.g., relational databases, external search APIs) can be added simply by registering a new `RetrievalCreator` without modifying the core `RAGService`.
    * **Optimized Latency:** The `HybridRetrievalStrategy` executes its sub-strategies in parallel, ensuring that the addition of the Graph traversal does not strictly compound with the Vector search latency.
    * **Separation of Concerns:** Each `RetrievalCreator` is entirely responsible for resolving its own infrastructure dependencies (like specific LLMs or Prompt Services), keeping the `RAGFactory` clean.
* **Negative:**
    * **Configuration Complexity:** The polymorphic structure requires more deeply nested configuration files (e.g., configuring `vector` and `graph` sub-blocks under `hybrid`), which increases the cognitive load for system operators.
    * **Debugging Challenges:** Tracing the exact source of an answer in a hybrid, dynamically weighted fusion scenario can be opaque without relying heavily on the newly introduced OpenTelemetry spans.
* **Neutral/Other:**
    * **Strict Protocol Adherence:** All future retrieval strategies are forced to implement the `RetrievalCreator` protocol to participate in the ecosystem.