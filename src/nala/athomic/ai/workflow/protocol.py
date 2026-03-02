from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .definition.protocol import WorkflowDefinitionProtocol


@runtime_checkable
class WorkflowEngineProtocol(Protocol):
    """
    Contract for any provider that can execute a workflow.
    """

    def compile(self, definition: WorkflowDefinitionProtocol) -> Any:
        """
        Compiles the generic definition into an executable format.

        Args:
            definition: The generic blueprint of the workflow.

        Returns:
            The compiled, provider-specific executable object.
        """
        ...

    async def run(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the workflow.

        Args:
            input_data: The initial state/input variables.
            config: Runtime configuration (e.g., thread_id, callbacks).

        Returns:
            The final state of the workflow after execution.
        """
        ...
