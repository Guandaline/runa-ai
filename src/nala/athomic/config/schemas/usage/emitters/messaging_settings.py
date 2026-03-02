from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.enums.defaults import Defaults


class MessagingUsageEmitterSettings(BaseModel):
    """
    Defines configuration for messaging-based usage emission.

    This settings model declares how usage events are emitted through
    the messaging subsystem, including the connection used to resolve
    the underlying messaging backend.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    backend: Literal["messaging"] = Field(
        default="messaging",
        alias="BACKEND",
        description="The usage emission backend type for messaging emitters.",
    )

    enabled: Optional[bool] = Field(
        default=True,
        alias="ENABLED",
        description="Enable or disable messaging-based usage emission.",
    )

    connection_name: Optional[str] = Field(
        default=Defaults.DEFAULT_MESSAGING_CONNECTION,
        alias="CONNECTION_NAME",
        description=(
            "Name of the messaging connection used for usage emission. "
            "The actual backend is resolved by the messaging layer."
        ),
    )

    topic: Optional[str] = Field(
        default="platform.usage.events.v1",
        alias="TOPIC",
        description="The topic name where usage events will be published.",
    )

    auto_create_topic: Optional[bool] = Field(
        default=True,
        alias="AUTO_CREATE_TOPIC",
        description="Whether to automatically create the topic if it does not exist.",
    )
