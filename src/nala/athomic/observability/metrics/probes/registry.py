# src/nala/athomic/observability/metrics/probes/registry.py
from nala.athomic.base import BaseInstanceRegistry

from ..protocol import MetricProbe


class ProbeRegistry(BaseInstanceRegistry[MetricProbe]):
    """
    A central registry for holding active, instance-based metric probes.

    The MetricScheduler uses this registry to discover which probes to run
    during its collection cycle.
    """

    pass


# Create a singleton instance for the application to use
probe_registry = ProbeRegistry(
    protocol=MetricProbe,
)
