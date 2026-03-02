from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NoopSettings(BaseModel):
    """
    Placeholder settings for a no-operation usage emitter.

    This model exists to fulfill the schema requirements when
    no usage emission is desired.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    backend: Literal["noop"] = Field(
        default="noop",
        alias="BACKEND",
        description="The usage emission backend type for noop emitter.",
    )
