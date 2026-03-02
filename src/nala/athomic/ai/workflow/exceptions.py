from ..exceptions import AIError


class WorkflowError(AIError):
    """
    Base exception for all workflow-related errors.
    """

    pass


class WorkflowDefinitionError(WorkflowError):
    """
    Raised when there is an issue with the graph structure definition.
    Examples: Missing entry point, isolated nodes, invalid edge targets.
    """

    pass


class WorkflowExecutionError(WorkflowError):
    """
    Raised when the workflow fails during runtime.
    """

    pass


class NodeExecutionError(WorkflowExecutionError):
    """
    Raised when a specific step (node) fails to execute.
    """

    def __init__(self, node_name: str, original_error: Exception) -> None:
        super().__init__(f"Error executing node '{node_name}': {str(original_error)}")
        self.node_name = node_name
        self.original_error = original_error
