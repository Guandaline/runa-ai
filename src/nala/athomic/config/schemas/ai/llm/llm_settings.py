# src/nala/athomic/config/schemas/ai/llm_settings.py
"""
Defines the Pydantic schemas for LLM (Large Language Model) provider configurations.

This module contains the schemas for specific providers (OpenAI, Vertex, etc.)
as well as the unified connection settings that group provider details with
generation parameters (temperature, tokens, etc.).
"""

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .generation_settings import GenerationSettings
from .providers import (
    AzureOpenAIProviderSettings,
    GoogleGenAIProviderSettings,
    OllamaProviderSettings,
    OpenAIProviderSettings,
)

# Polymorphic Union for Providers
ProviderConfigTypes = Annotated[
    Union[
        GoogleGenAIProviderSettings,
        OpenAIProviderSettings,
        OllamaProviderSettings,
        AzureOpenAIProviderSettings,
    ],
    Field(discriminator="backend"),
]


class LLMConnectionSettings(BaseModel):
    """
    Defines the configuration for a single AI/LLM connection.

    This model serves as a container that groups the provider-specific connection
    details (e.g., credentials, endpoints) with the operational parameters
    (e.g., timeouts, retries) and the generative parameters (e.g., temperature).

    Attributes:
        enabled (bool): Enables or disables this specific AI connection.
        backend (str): The backend provider identifier (discriminator).
        default_model (str): The default model ID to use (e.g., 'gpt-4', 'gemini-pro').
        default_embedding_model (Optional[str]): The default embedding model ID.
        max_retries (int): Maximum number of retry attempts for failed requests.
        timeout (float): Request timeout in seconds.
        generation (GenerationSettings): Default generation parameters (temperature, etc.).
        provider (ProviderConfigTypes): The provider-specific configuration.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enables or disables this specific AI connection.",
    )

    backend: Literal["google_genai", "openai", "azure", "ollama"] = Field(
        ...,
        alias="BACKEND",
        description="The backend provider identifier (discriminator).",
    )

    connection_name: Optional[str] = Field(
        default=None,
        alias="CONNECTION_NAME",
        description="The unique name of this connection, injected by the manager at runtime.",
    )

    default_model: str = Field(
        ...,
        alias="DEFAULT_MODEL",
        description="The default model ID to use for this connection (e.g., 'gpt-4', 'gemini-pro').",
    )

    default_embedding_model: Optional[str] = Field(
        default=None,
        alias="DEFAULT_EMBEDDING_MODEL",
        description="The default embedding model to use for this connection, if applicable.",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        alias="MAX_RETRIES",
        description="The maximum number of retry attempts for failed API calls.",
    )

    timeout: float = Field(
        default=30.0,
        gt=0,
        alias="TIMEOUT",
        description="The default request timeout in seconds.",
    )

    generation: GenerationSettings = Field(
        default_factory=GenerationSettings,
        alias="GENERATION",
        description="Default generation parameters (temperature, max_tokens, etc.) for this connection.",
    )

    provider: ProviderConfigTypes = Field(
        ...,
        alias="PROVIDER",
        description="The provider-specific configuration settings (e.g. credentials).",
    )
