from .ai import (
    agent_checkpoint_duration_seconds,
    agent_checkpoint_operations_total,
    agent_checkpoint_size_bytes,
    ai_document_chunks_created_total,
    ai_document_ingestion_duration_seconds,
    ai_document_ingestion_operations_total,
    ai_document_loader_duration_seconds,
    ai_document_pages_loaded_total,
    ai_document_splitter_duration_seconds,
    ai_semantic_cache_lookup_duration_seconds,
    ai_semantic_cache_lookup_total,
    ai_semantic_cache_saved_tokens_total,
    ai_semantic_cache_write_total,
    cognitive_classification_duration_seconds,
    cognitive_classification_total,
    cognitive_confidence_score,
    cognitive_intent_detected_total,
    embedding_operation_duration_seconds,
    embedding_operations_total,
    embedding_token_usage_total,
    llm_operation_duration_seconds,
    llm_operations_total,
    llm_token_usage_total,
    rag_empty_context_total,
    rag_hyde_generation_duration_seconds,
    rag_operation_duration_seconds,
    rag_operations_total,
    rag_rerank_duration_seconds,
    rag_reranked_documents_count,
    rag_retrieved_chunks_count,
    workflow_execution_duration_seconds,
    workflow_executions_total,
    workflow_step_duration_seconds,
    workflow_step_errors_total,
    workflow_steps_count,
)
from .api_routes_metrics import (
    api_route_request_duration_seconds,
    api_route_requests_total,
)
from .base_metrics import in_progress_requests, request_counter, request_duration
from .cache_metrics import (
    cache_background_refreshes_total,
    cache_error_counter,
    cache_hit_counter,
    cache_miss_counter,
    cache_stale_hits_total,
)
from .database_metrics import (
    kvstore_operation_duration_seconds,
    kvstore_operations_total,
)

from .rate_limiter_metrics import rate_limiter_allowed_total, rate_limiter_blocked_total
from .retry_metrics import (
    retry_attempts_total,
    retry_circuit_breaker_aborts_total,
    retry_failures_total,
)

from .service_lifecycle_metrics import (
    service_connection_attempts_total,
    service_connection_failures_total,
    service_connection_status,
    service_readiness_status,
)

from .vector_metrics import (
    vector_db_operation_duration_seconds,
    vector_db_operations_total,
)

from .locking_metrics import (
    locking_attempts_total,
    locking_hold_duration_seconds,
)

__all__ = [
    # AI
    # AI Document Ingestion Metrics
    "ai_document_ingestion_operations_total",
    "ai_document_ingestion_duration_seconds",
    "ai_document_loader_duration_seconds",
    "ai_document_splitter_duration_seconds",
    "ai_document_pages_loaded_total",
    "ai_document_chunks_created_total",
    # Semantic Cache Metrics
    "ai_semantic_cache_lookup_total",
    "ai_semantic_cache_lookup_duration_seconds",
    "ai_semantic_cache_saved_tokens_total",
    "ai_semantic_cache_write_total",
    # AI Cognitive Metrics
    "cognitive_classification_duration_seconds",
    "cognitive_classification_total",
    "cognitive_intent_detected_total",
    "cognitive_confidence_score",
    # Agent Persistence Metrics
    "agent_checkpoint_operations_total",
    "agent_checkpoint_duration_seconds",
    "agent_checkpoint_size_bytes",
    # Embedding Metrics
    "embedding_operation_duration_seconds",
    "embedding_operations_total",
    "embedding_token_usage_total",
    # LLM Metrics
    "llm_operation_duration_seconds",
    "llm_operations_total",
    "llm_token_usage_total",
    # Rag Metrics
    "rag_operation_duration_seconds",
    "rag_operations_total",
    "rag_retrieved_chunks_count",
    "rag_empty_context_total",
    "rag_hyde_generation_duration_seconds",
    "rag_reranked_documents_count",
    "rag_rerank_duration_seconds",
    # Workflow Metrics
    "workflow_execution_duration_seconds",
    "workflow_executions_total",
    "workflow_steps_count",
    "workflow_step_duration_seconds",
    "workflow_step_errors_total",

    # API Route Metrics
    "api_route_requests_total",
    "api_route_request_duration_seconds",
   
    # Base Metrics
    "request_counter",
    "request_duration",
    "in_progress_requests",

    # Cache Metrics
    "cache_hit_counter",
    "cache_miss_counter",
    "cache_error_counter",
    "cache_stale_hits_total",
    "cache_background_refreshes_total",
    
    # Locking Metrics
    "locking_attempts_total",
    "locking_hold_duration_seconds",

    # Database Metrics
    "kvstore_operation_duration_seconds",
    "kvstore_operations_total",
    "vector_db_operation_duration_seconds",
    "vector_db_operations_total",
    
    # Rate Limiter Metrics
    "rate_limiter_blocked_total",
    "rate_limiter_allowed_total",
    # Retry Metrics
    "retry_attempts_total",
    "retry_failures_total",
    "retry_circuit_breaker_aborts_total",

    # Service Lifecycle Metrics
    "service_connection_attempts_total",
    "service_connection_failures_total",
    "service_connection_status",
    "service_readiness_status",
]
