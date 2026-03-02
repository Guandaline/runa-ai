"""
Defines the Pydantic schemas for OpenAI provider configurations.
"""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.models import secrets_types


class OpenAIProviderSettings(BaseModel):
    """Configuration settings specific to the OpenAI API provider."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["openai"] = Field(
        "openai", description="Discriminator field for OpenAI."
    )

    api_key: secrets_types = Field(
        ..., alias="API_KEY", description="The OpenAI API Key."
    )
    organization_id: Optional[str] = Field(
        default=None,
        alias="ORG_ID",
        description="The optional Organization ID for OpenAI.",
    )

    base_url: Optional[str] = Field(
        default=None,
        alias="BASE_URL",
        description="The base URL for the API.",
    )

    def get_client_params(self) -> Dict[str, Any]:
        """
        Returns parameters for initializing the OpenAI client.
        Standard implementation passes fields directly.
        """
        return {
            "api_key": self.api_key.get_secret_value(),
            "organization": self.organization_id,
            "base_url": self.base_url,
        }
