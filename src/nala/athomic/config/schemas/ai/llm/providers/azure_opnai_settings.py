from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.models import secrets_types


class AzureOpenAIProviderSettings(BaseModel):
    """Configuration settings specific to the Azure OpenAI Service provider."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["azure"] = Field(
        "azure", description="Discriminator field for Azure OpenAI."
    )

    api_key: secrets_types = Field(
        ..., alias="API_KEY", description="The Azure OpenAI API Key."
    )
    endpoint: str = Field(
        ..., alias="ENDPOINT", description="The full Azure Endpoint URL."
    )
    api_version: str = Field(
        default="2023-05-15",
        alias="API_VERSION",
        description="The Azure API version to use.",
    )
    deployment_name: str = Field(
        ...,
        alias="DEPLOYMENT_NAME",
        description="The name of the model deployment in Azure.",
    )

    def get_client_params(self) -> Dict[str, Any]:
        """
        Returns parameters for initializing the Azure OpenAI client.
        """
        return {
            "api_key": self.api_key.get_secret_value(),
            "azure_endpoint": self.endpoint,
            "api_version": self.api_version,
            "azure_deployment": self.deployment_name,
        }
