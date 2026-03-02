from enum import Enum, auto


class ServiceState(Enum):
    """Defines the discrete stages in the lifecycle of a managed service.

    These states are tracked by the BaseService class and govern when a service
    is safe to interact with or needs recovery.

    Attributes:
        PENDING: The service object has been instantiated but not yet started.
        CONNECTING: The service is currently executing its asynchronous connection logic (`_connect`).
        READY: The service is connected, initialized, and available for operations (Public Readines Check).
        FAILED: A connection or critical startup failure occurred.
        CLOSED: The service has been gracefully and permanently shut down (`close()`/`stop()`).
        RUNNING: The service is executing its continuous background task (`_run_loop`).
    """

    PENDING = auto()
    CONNECTING = auto()
    READY = auto()
    FAILED = auto()
    CLOSED = auto()
    RUNNING = auto()
