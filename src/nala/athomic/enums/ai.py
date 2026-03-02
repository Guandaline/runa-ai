# src/nala/athomic/enums/ai.py
from enum import Enum


class FusionAlgorithm(str, Enum):
    """
    Standardized enumeration for RAG hybrid fusion algorithms.
    """

    RRF = "rrf"
    WEIGHTED = "weighted"
