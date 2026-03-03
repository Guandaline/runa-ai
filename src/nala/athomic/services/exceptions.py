#
# src/nala/athomic/services/exceptions.py
#
from typing import Optional

from nala.athomic.base.exceptions import AthomicError


class ServiceError(AthomicError):
    """Base exception for all service-related errors."""

    def __init__(
        self, message: str, service_name: Optional[str] = None, *args, **kwargs
    ):
        self.message = message
        self.service_name = service_name
        self.details = kwargs

        super().__init__(message, *args)


class ServiceConnectionError(ServiceError):
    """Raised when a service fails to connect to its underlying dependency."""

    def __init__(self, service_name: str, message: str = "Connection failed."):
        super().__init__(message=message, service_name=service_name)


class ServiceAlreadyRunningError(ServiceError):
    """Raised when an attempt is made to start a service that is already running or has been stopped."""

    def __init__(self, service_name: str):
        super().__init__(
            message="Service is already running or has been closed.",
            service_name=service_name,
        )


class ServiceUnavailableError(ServiceError):
    """Raised when an operation is attempted on a service that is not available."""

    def __init__(
        self, service_name: str, message: str = "The service is not available."
    ):
        super().__init__(message=message, service_name=service_name)


class ServiceNotReadyError(ServiceUnavailableError):
    """
    Raised when an operation is attempted on a service that has not yet
    completed its startup and become ready.
    """

    def __init__(self, service_name: str):
        super().__init__(
            service_name=service_name,
            message="The service is not ready to perform this operation.",
        )


class ProviderError(ServiceError):
    """
    Generic error raised when an underlying provider (3rd party lib/API) fails.
    This wraps the original exception (e.g., qdrant_client.UnexpectedResponse).
    """

    pass


class ProviderConnectionError(ProviderError):
    """
    Raised when a connection to the provider cannot be established.
    Examples: Timeouts, DNS failures, Connection Refused.
    """

    pass


class ProviderInitializationError(ServiceError):
    """Raised when a provider fails to initialize its internal components."""

    def __init__(self, service_name: str, reason: str):
        super().__init__(
            message=f"Failed to initialize provider: {reason}",
            service_name=service_name,
        )


class ResourceNotFoundError(ServiceError):
    """
    Raised when a requested resource (e.g., Collection, Index, Table) does not exist.
    """

    pass
