# src/nala/athomic/observability/tracing/attributes/graph_attrs.py
from enum import Enum


class GraphTracingAttributes(Enum):
    """
    Defines tracing attribute keys specifically for the Graph AI module.
    """

    # Input Attributes
    INPUT_LENGTH = "graph.input_length"  # Size of the text being processed

    # Entity/Relationship Counts
    NODES_COUNT = "graph.nodes_count"  # Number of nodes involved/extracted
    EDGES_COUNT = "graph.edges_count"  # Number of edges involved/extracted

    # Query Context
    NODE_ID = "graph.node_id"  # Target node identifier
    DEPTH = "graph.depth"  # Traversal depth

    # Result Metrics
    RESULT_COUNT = "graph.result_count"  # Generic count of results (nodes/edges found)
