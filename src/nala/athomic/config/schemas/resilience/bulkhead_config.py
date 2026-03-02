# src/nala/athomic/config/schemas/resilience/bulkhead_config.py
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BulkheadSettings(BaseModel):
    """Defines the configuration for the Bulkhead resilience pattern.

    This model configures the bulkhead mechanism, which limits the number of
    concurrent executions for specific operations. This isolates different parts
    of the system to prevent a failure or slowdown in one area from cascading
    and affecting the entire application.

    Attributes:
        enabled (bool): A master switch for the bulkhead system.
        default_limit (int): The default concurrency limit if no specific
            policy is defined.
        policies (Optional[Dict[str, int]]): A dictionary mapping policy names
            to their specific concurrency limits.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="BULKHEAD_ENABLED",
        description="A master switch to globally enable or disable the bulkhead system.",
    )

    default_limit: int = Field(
        default=10,
        alias="BULKHEAD_DEFAULT_LIMIT",
        description="The default concurrency limit to apply to an operation if no specific policy is defined for it.",
    )

    policies: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        alias="BULKHEAD_POLICIES",
        description="A dictionary that maps policy names to their specific concurrency limits (e.g., {'payment_api': 5, 'external_report': 2}).",
    )
