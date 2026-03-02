from enum import Enum


class UsageTracingAttributes(Enum):
    """
    Defines tracing attribute keys specifically for the Usage module.
    """

    # Context Attributes
    SOURCE = "usage.source"
    EXECUTION_ID = "usage.execution_id"
    TENANT_ID = "usage.tenant_id"
    USER_ID = "usage.user_id"
    SESSION_ID = "usage.session_id"
    CORRELATION_ID = "usage.correlation_id"

    # Payload Attributes
    UNIT = "usage.unit"
    QUANTITY = "usage.quantity"

    # Event Names
    EMIT = "usage.emit"
