# src/nala/athomic/enums/events.py
"""Defines standardized enumeration for internal event names."""

from enum import Enum


class InternalEvents(str, Enum):
    """
    Defines standardized string constants for internal events used by the event bus.

    This ensures that publishers and subscribers use the same event names,
    preventing decoupling issues caused by typos.
    """

    CONFIG_UPDATED = "config.updated"
