from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class WorkflowNodeProtocol(Protocol):
    """
    Defines the contract for a single unit of work (Node) in a workflow.
    """

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the node logic.

        Args:
            state: The current state of the workflow execution.

        Returns:
            A dictionary containing updates to be merged into the state.
        """
        ...
