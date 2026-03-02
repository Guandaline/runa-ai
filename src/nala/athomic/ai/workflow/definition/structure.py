from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

from ..types import S


class ConditionalRoute(NamedTuple):
    """Represents a dynamic decision point in the graph."""

    source: str
    condition_fn: Callable[[S], str]
    destinations: Dict[str, str]


class WorkflowDefinition:
    """
    Standard implementation of the workflow structure.

    Acts as an Intermediate Representation (IR) of the graph.
    It stores nodes and edges in memory so that an Engine (Provider)
    can read them and compile the actual execution graph.
    """

    def __init__(self) -> None:
        # Stores step logic: { "step_name": handler_function }
        self.steps: Dict[str, Callable[..., Any]] = {}

        # Stores entry point name
        self.entry_point: Optional[str] = None

        # Stores direct edges: [ ("start_node", "end_node"), ... ]
        self.routes: List[Tuple[str, str]] = []

        # Stores conditional edges
        self.conditional_routes: List[ConditionalRoute] = []

    def add_step(self, name: str, handler: Callable[..., Any]) -> None:
        """Registers a node."""
        if name in self.steps:
            raise ValueError(f"Step '{name}' is already defined.")
        self.steps[name] = handler

    def set_entry_point(self, step_name: str) -> None:
        """Sets the starting node."""
        if step_name not in self.steps:
            raise ValueError(f"Entry point '{step_name}' must be defined in steps.")
        self.entry_point = step_name

    def add_route(self, source: str, destination: str) -> None:
        """Adds a linear edge."""
        self.routes.append((source, destination))

    def add_conditional_route(
        self,
        source: str,
        condition_fn: Callable[[S], str],
        destinations: Dict[str, str],
    ) -> None:
        """Adds a branching logic."""
        self.conditional_routes.append(
            ConditionalRoute(source, condition_fn, destinations)
        )
