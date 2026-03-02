"""
Defines the Pydantic schemas for the Ollama provider configurations.
"""

from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class OllamaProviderSettings(BaseModel):
    """Configuration settings specific to the local Ollama provider."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["ollama"] = Field(
        "ollama", description="Discriminator field for Ollama."
    )

    base_url: str = Field(
        default="http://localhost:11434",
        alias="BASE_URL",
        description="The URL where the Ollama service is running.",
    )

    api_key: str = Field(
        default="ollama",  # pragma: allowlist secret
        alias="API_KEY",
        description="Ollama does not require an API key; this is a placeholder.",
    )

    def get_client_params(self) -> Dict[str, Any]:
        """
        Returns parameters for initializing the OpenAI client compatible with Ollama.
        Applies necessary normalization (e.g., ensuring /v1 suffix).
        """
        url = self.base_url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"

        return {
            "api_key": self.api_key,
            "base_url": url,
            "organization": None,
        }
