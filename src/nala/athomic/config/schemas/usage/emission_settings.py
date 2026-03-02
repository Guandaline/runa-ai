from typing import Annotated, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.usage.emitters import (
    MessagingUsageEmitterSettings,
    NoopSettings,
)

# Polymorphic Union for Providers
EmitterSettingsTypes = Annotated[
    Union[MessagingUsageEmitterSettings, NoopSettings],
    Field(discriminator="backend"),
]


class UsageEmissionSettings(BaseModel):
    """
    Declares and configures usage emission backends.

    This settings model aggregates typed emitter configurations, following
    the same structural pattern used across the Athomic platform for
    provider-specific settings (e.g. database, messaging, rate limiter).
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )

    provider: Optional[EmitterSettingsTypes] = Field(
        default_factory=NoopSettings,
        alias="PROVIDER",
        description="Configuration for messaging-based usage emission.",
    )
