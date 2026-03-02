# src/nala/athomic/observability/metrics/protocol.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricProbe(Protocol):
    """
    Defines the contract for a component that periodically collects and
    updates specific application metrics (Probes).

    Any class implementing this protocol can be scheduled for asynchronous
    execution by a MetricScheduler service.
    """

    name: str
    """A unique, human-readable name identifying the metric probe (e.g., 'cpu_usage_probe')."""

    async def update(self) -> None:
        """
        Executes the metric collection logic (e.g., reads a value, calculates a delta)
        and updates the corresponding Prometheus collector.

        This method must be non-blocking (asynchronous).
        """
        ...
