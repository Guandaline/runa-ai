from prometheus_client import Gauge

from nala.athomic.observability.metrics.protocol import MetricProbe
from nala.athomic.services.protocol import BaseServiceProtocol


class ServiceHealthProbe(MetricProbe):
    """
    A generic MetricProbe that checks the health of any service
    implementing the ServiceProtocol.

    It updates a provided Prometheus Gauge based on the readiness
    state of the service.
    """

    def __init__(self, service: BaseServiceProtocol, health_gauge: Gauge):
        """
        Initializes the health probe for a specific service.

        Args:
            service: The service instance to be monitored.
                     Must follow the ServiceProtocol.
            health_gauge: The Prometheus Gauge to be updated with the status (0 or 1).
        """
        self._service = service
        self._gauge = health_gauge
        # The probe name is the same as the service it monitors.
        self.name = self._service.service_name

    async def update(self) -> None:
        """
        Checks the service state and updates the Gauge with 3 states:
        -  1: Enabled and Ready (UP)
        -  0: Enabled and Not Ready (DOWN)
        - -1: Disabled (DISABLED)
        """
        try:
            if not self._service.is_enabled():
                # The service is intentionally disabled.
                self._gauge.set(-1)
                return

            # If we reach here, the service is enabled.
            # Check if it is ready to operate.
            if self._service.is_ready():
                # Enabled and ready.
                self._gauge.set(1)
            else:
                # Enabled, but not ready (e.g., connection failure).
                # This is a real failure state.
                self._gauge.set(0)

        except Exception:
            # Any exception during the check indicates a failure.
            # If the service is enabled, this is a problem.
            if self._service.is_enabled():
                self._gauge.set(0)
            else:
                # If an error occurred but the service was disabled,
                # just mark as disabled.
                self._gauge.set(-1)
