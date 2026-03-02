from .ai import GraphTracingAttributes
from .usage_attrs import UsageTracingAttributes

__all__ = [
    "UsageTracingAttributes",
    "GraphTracingAttributes",
]


# src/nala/athomic/observability/tracing/attributes.py
"""
Defines constants for OpenTelemetry span attribute names,
following semantic conventions for databases, messaging, and storage systems.

Using these constants ensures consistent naming conventions across all
instrumented parts of the Athomic engine.
"""

# ------ AI Attributes ------
AI_SYSTEM = "ai.system"  # Semantic convention: The AI system/vendor, e.g., "openai", "vertex_ai"
AI_MODEL = "ai.model"  # Semantic convention: The specific model being used, e.g., "gpt-4", "gemini-pro"
AI_BATCH_SIZE = (
    "ai.batch_size"  # Non-standard: The number of items processed in a batch operation
)

# LLM-specific attributes (following OpenTelemetry semantic conventions for GenAI)
LLM_SYSTEM = "llm.system"  # The LLM system/vendor, e.g., "openai", "anthropic"
LLM_MODEL = "llm.model"  # The specific model being used, e.g., "gpt-4", "claude-3"
LLM_PROVIDER = "llm.provider"  # The backend provider for the LLM service


# --- Database Attributes ---

DB_SYSTEM = "db.system"  # Semantic convention: The database vendor, e.g., "mongodb", "redis", "postgresql"
DB_OPERATION = "db.operation"  # Semantic convention: The operation being performed, e.g., "save", "find_by_id", "delete"
DB_STATEMENT = "db.statement"  # Semantic convention: The query string or unique identifier, e.g., "id=123"
DB_KEY = "db.key"  # Non-standard: The specific key being operated on (useful for KV stores). # pragma: allowlist secret
DB_STATUS = "db.status"  # Non-standard: Operation status, complementing db.operation, e.g., "hit", "miss"

# --- Messaging Attributes ---

MESSAGING_SYSTEM = "messaging.system"  # Semantic convention: The messaging system vendor, e.g., "kafka", "sqs"
MESSAGING_DESTINATION = (
    "messaging.destination"  # Semantic convention: The topic or queue name
)
MESSAGING_OPERATION = "messaging.operation"  # Semantic convention: The role of the span, e.g., "process", "publish"
MESSAGING_CONSUMER_ID = "messaging.consumer_id"  # Non-standard/Extension: Identifier for the consumer group/instance

# --- Storage Attributes ---

STORAGE_PROVIDER = (
    "storage.provider"  # The storage system vendor, e.g., "aws_s3", "gcp_gcs"
)
STORAGE_DESTINATION_PATH = "storage.destination_path"  # Path/URI for write operations
STORAGE_SOURCE_PATH = "storage.source_path"  # Path/URI for read operations
STORAGE_PATH = "storage.path"  # Generic Path/URI

# --- Workflow Attributes ---

WORKFLOW_ID = "workflow.id"
WORKFLOW_NAME = "workflow.name"
WORKFLOW_RUN_ID = "workflow.run_id"
WORKFLOW_TASK_QUEUE = "workflow.task_queue"
WORKFLOW_SIGNAL_NAME = "workflow.signal"
