# src/nala/athomic/observability/metrics/usage/ai/rag_metrics.py
from prometheus_client import Counter, Histogram

from nala.athomic.observability.metrics.enums import MetricNamespace

_NAMESPACE = MetricNamespace.AI.value
_SUBSYSTEM = "rag"

# --- Core RAG Metrics ---

rag_operation_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_operation_duration_seconds",
    documentation="Time spent in RAG operations (retrieve, augment, generate).",
    labelnames=["operation", "status"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

rag_operations_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_operations_total",
    documentation="Total count of RAG operations executed.",
    labelnames=["operation", "status"],
)

rag_retrieved_chunks_count = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_retrieved_chunks_count",
    documentation="Distribution of the number of chunks retrieved per query.",
    buckets=(0, 1, 3, 5, 10, 20),
)

rag_empty_context_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_empty_context_total",
    documentation="Count of queries that resulted in zero retrieved documents (context miss).",
)

# --- Advanced RAG Extensions (Phase 4.2) ---

rag_rerank_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_rerank_duration_seconds",
    documentation="Time spent in the Cross-Encoder re-ranking phase.",
    labelnames=["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

rag_reranked_documents_count = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_reranked_documents_count",
    documentation="Number of documents retained after re-ranking.",
    buckets=(0, 1, 3, 5, 10),
)

rag_hyde_generation_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_hyde_generation_duration_seconds",
    documentation="Time spent generating the hypothetical document for HyDE.",
    buckets=(0.5, 1.0, 2.0, 4.0, 8.0, 15.0),
)


# --- Hybrid Fusion Metrics ---

rag_fusion_duration_seconds = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_fusion_duration_seconds",
    documentation="Time spent in the hybrid fusion phase (RRF, Weighted, etc).",
    labelnames=["strategy", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

rag_fusion_intersection_total = Counter(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_fusion_intersection_total",
    documentation="Total count of documents found in multiple retrieval paths (consensus level).",
    labelnames=["strategy"],
)

rag_fusion_source_contribution_count = Histogram(
    name=f"{_NAMESPACE}_{_SUBSYSTEM}_fusion_source_contribution_count",
    documentation="Number of documents from a specific source (vector/graph) that made it to the final top-k.",
    labelnames=["strategy", "source_type"],
    buckets=(0, 1, 3, 5, 10, 20),
)
