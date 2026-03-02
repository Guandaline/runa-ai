"""
Workflow Orchestration Module.

This module provides the core abstractions for defining and executing
AI agent workflows (Directed Cyclic Graphs, State Machines, or Linear Chains).
It uses a provider-agnostic approach, allowing the underlying execution engine
(e.g., LangGraph, LangChain, or simple in-memory loops) to be swapped via adapters.
"""

from .base import BaseWorkflowEngine
from .definition.protocol import WorkflowDefinitionProtocol
from .definition.structure import WorkflowDefinition
from .exceptions import (
    NodeExecutionError,
    WorkflowDefinitionError,
    WorkflowError,
    WorkflowExecutionError,
)
from .node import WorkflowNodeProtocol
from .protocol import WorkflowEngineProtocol
from .providers import InMemoryWorkflowEngine, LangGraphWorkflowEngine
from .types import WorkflowStatus

__all__ = [
    # Core Types
    "WorkflowStatus",
    # Protocols (Contracts)
    "WorkflowNodeProtocol",
    "WorkflowDefinitionProtocol",
    "WorkflowEngineProtocol",
    # Implementations (Foundations)
    "WorkflowDefinition",
    "BaseWorkflowEngine",
    # Exceptions
    "WorkflowError",
    "WorkflowDefinitionError",
    "WorkflowExecutionError",
    "NodeExecutionError",
    # Providers
    "InMemoryWorkflowEngine",
    "LangGraphWorkflowEngine",
]
