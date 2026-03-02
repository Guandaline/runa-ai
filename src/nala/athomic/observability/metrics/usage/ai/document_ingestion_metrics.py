# src/nala/athomic/observability/metrics/usage/document_ingestion_metrics.py
"""
Prometheus metrics for the AI Document Ingestion pipeline.
Captures throughput, latency, and volume (pages/chunks) of ingested documents
specifically for Semantic Memory / RAG contexts.
"""

from prometheus_client import Counter, Histogram

# Total number of ingestion requests
ai_document_ingestion_operations_total = Counter(
    "nala_ai_document_ingestion_operations_total",
    "Total number of AI document ingestion requests attempted.",
    ["extension", "status"],  # status: success, failure
)

# Latency of the full ingestion process
ai_document_ingestion_duration_seconds = Histogram(
    "nala_ai_document_ingestion_duration_seconds",
    "Time spent performing full AI document ingestion (Load + Split + Embed + Store).",
    ["extension"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

# Granular Latency: Parsing/Loading
ai_document_loader_duration_seconds = Histogram(
    "nala_ai_document_loader_duration_seconds",
    "Time spent loading/parsing the raw file content.",
    ["loader_type"],
)

# Granular Latency: Splitting
ai_document_splitter_duration_seconds = Histogram(
    "nala_ai_document_splitter_duration_seconds",
    "Time spent splitting text into chunks.",
    ["splitter_type"],
)

# Volume Metrics
ai_document_pages_loaded_total = Counter(
    "nala_ai_document_pages_loaded_total",
    "Total number of pages (or document units) loaded for AI processing.",
    ["extension"],
)

ai_document_chunks_created_total = Counter(
    "nala_ai_document_chunks_created_total",
    "Total number of semantic chunks generated.",
    ["extension"],
)
