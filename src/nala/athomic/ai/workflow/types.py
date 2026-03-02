from enum import Enum
from typing import Any, Dict, TypeVar

# Generic type variable for workflow state.
# This ensures that specific implementations can enforce state structure
# while the core remains agnostic (treating it as a Dict).
S = TypeVar("S", bound=Dict[str, Any])


class WorkflowStatus(Enum):
    """
    Represents the current lifecycle status of a workflow execution.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"
