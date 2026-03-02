"""
Defines the Pydantic schemas for Google GenAI (Gemini) provider configurations.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from nala.athomic.config.schemas.models import secrets_types


class GoogleGenAIProviderSettings(BaseModel):
    """
    Configuration settings for Google's GenAI (Gemini) models.

    Supports both:
    1. **Vertex AI (GCP):** Requires `project_id` and `location`.
    2. **AI Studio:** Requires `api_key`.

    The validator ensures the correct combination of fields is present.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["google_genai", "vertex"] = Field(
        default="google_genai",
        description="Discriminator field. Use 'vertex' for legacy config compatibility.",
    )

    # --- Mode: AI Studio ---
    api_key: Optional[secrets_types] = Field(
        default=None,
        alias="API_KEY",
        description="Google AI Studio API Key. Required if not using Vertex AI.",
    )

    # --- Mode: Vertex AI ---
    project_id: Optional[str] = Field(
        default=None,
        alias="PROJECT_ID",
        description="The Google Cloud Project ID. Required for Vertex AI mode.",
    )
    location: Optional[str] = Field(
        default=None,
        alias="LOCATION",
        description="The Google Cloud region (e.g., 'us-central1'). Required for Vertex AI mode.",
    )
    service_account_json: Optional[secrets_types] = Field(
        default=None,
        alias="SERVICE_ACCOUNT_JSON",
        description="Path or content of the Service Account JSON. If None, ADC is used (Vertex mode).",
    )

    default_model: str = Field(
        default="gemini-1.5-flash",
        alias="DEFAULT_MODEL",
        description="The model name to use (e.g., 'gemini-1.5-pro', 'gemini-1.0-pro').",
    )

    @model_validator(mode="after")
    def validate_auth_method(self) -> Self:
        """
        Validates that either API Key (Studio) or Project/Location (Vertex) are provided.
        """
        has_api_key = self.api_key is not None
        has_vertex_creds = self.project_id is not None and self.location is not None

        if not has_api_key and not has_vertex_creds:
            raise ValueError(
                "Invalid Google GenAI configuration. "
                "Must provide either 'api_key' (for AI Studio) "
                "OR 'project_id' and 'location' (for Vertex AI)."
            )
        return self
