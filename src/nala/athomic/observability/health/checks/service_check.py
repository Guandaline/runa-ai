# src/nala/athomic/observability/health/checks/service_check.py
from nala.athomic.services.protocol import BaseServiceProtocol

from ..protocol import ReadinessCheck


class ServiceReadinessCheck(ReadinessCheck):
    """
    A generic readiness check implementation that verifies the health and
    readiness state of any core Athomic service implementing the BaseServiceProtocol.

    This check is a crucial part of the Dependency Inversion Principle,
    allowing the health system to query service status without knowing
    the service's internal implementation details.
    """

    def __init__(self, service: BaseServiceProtocol):
        """
        Initializes the check by injecting the service instance to be monitored.

        Args:
            service: The service instance (e.g., OutboxPublisher, HttpClient)
                     whose readiness state will be checked.
        """
        self._service = service
        # The check name is derived directly from the service name for clear reporting.
        self.name = self._service.service_name

    def enabled(self) -> bool:
        """
        Checks if the underlying service is enabled based on its configuration.

        Delegates the call directly to the service's `is_enabled()` method.
        """
        return self._service.is_enabled()

    async def check(self) -> bool:
        """
        Checks if the service is ready to operate (e.g., connected to its
        dependencies and initialized).

        Delegates the call directly to the service's `is_ready()` method.
        """
        # is_ready is asynchronous in BaseServiceProtocol, ensuring non-blocking check
        return self._service.is_ready()
