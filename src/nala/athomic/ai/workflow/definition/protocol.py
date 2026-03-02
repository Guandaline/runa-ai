from typing import Any, Callable, Dict, Protocol, runtime_checkable

from ..types import S


@runtime_checkable
class WorkflowDefinitionProtocol(Protocol):
    """
    Interface for defining the structure of a workflow.

    Acts as a platform-agnostic blueprint builder. Consumers use this
    interface to construct graphs without knowing if the underlying
    engine is LangGraph, LangChain, or a custom implementation.
    """

    def add_step(self, name: str, handler: Callable[..., Any]) -> None:
        """
        Registers a processing step (node) in the workflow.

        Args:
            name: Unique identifier for the step.
            handler: The function, callable, or Node instance to execute.
        """
        ...

    def set_entry_point(self, step_name: str) -> None:
        """
        Defines the starting node of the workflow.

        Args:
            step_name: The name of the node where execution begins.
        """
        ...

    def add_route(self, source: str, destination: str) -> None:
        """
        Adds a direct, unconditional transition between two steps.

        Args:
            source: The name of the source node.
            destination: The name of the target node.
        """
        ...

    def add_conditional_route(
        self,
        source: str,
        condition_fn: Callable[[S], str],
        destinations: Dict[str, str],
    ) -> None:
        """
        Adds dynamic branching logic based on the state.

        Args:
            source: The source node.
            condition_fn: A function that analyzes state and returns a route key.
            destinations: A map of {route_key: node_name} to resolve the next step.
        """
        ...
