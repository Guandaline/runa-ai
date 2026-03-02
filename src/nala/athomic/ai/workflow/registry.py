from nala.athomic.base.registry import BaseRegistry

from .protocol import WorkflowEngineProtocol
from .providers import InMemoryWorkflowEngine, LangGraphWorkflowEngine


class WorkflowEngineRegistry(BaseRegistry[WorkflowEngineProtocol]):
    """
    Registry for Workflow Engine implementations.

    Manages the registration and retrieval of workflow provider classes.
    It automatically registers the default in-memory provider upon initialization.
    """

    def register_defaults(self) -> None:
        """
        Registers the default 'memory' provider.
        """
        self.register("memory", InMemoryWorkflowEngine)
        self.register("langgraph", LangGraphWorkflowEngine)


# Global singleton instance
workflow_registry = WorkflowEngineRegistry(protocol=WorkflowEngineProtocol)
