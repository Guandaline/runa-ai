from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UsageAggregationSettings(BaseModel):
    """
    Defines configuration options for in-memory aggregation of usage events.

    This settings object controls how usage events are temporarily accumulated
    for snapshot generation, debugging, or downstream emission. It does not
    provide durability guarantees and does not implement any business logic.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enable or disable in-memory aggregation of usage events.",
    )

    window_seconds: Optional[int] = Field(
        default=None,
        alias="WINDOW_SECONDS",
        description=(
            "Optional sliding window size in seconds used to aggregate usage events. "
            "If not provided, aggregation is unbounded."
        ),
    )

    max_events_in_memory: int = Field(
        default=10_000,
        alias="MAX_EVENTS_IN_MEMORY",
        description=(
            "Maximum number of usage events kept in memory before older events "
            "are discarded to prevent unbounded memory growth."
        ),
    )
