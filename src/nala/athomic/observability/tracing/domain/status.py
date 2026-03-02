from enum import Enum


class TraceStatus(Enum):
    """
    Standardized values for operation status across the entire system.
    Use these values to ensure consistency in logs and spans.
    """

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TraceSource(Enum):
    """
    Standardized origins/sources for events to avoid magic strings.
    """

    INTERNAL_API = "internal_api"
    WORKER = "worker"
    CRON = "cron"
