from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from .loaders import FileSystemLoaderSettings


class PromptSettings(BaseModel):
    """
    Main configuration for the Prompts Module.
    Standardized name 'PromptSettings' to match 'DocumentsSettings'.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Master switch for the Prompts module.",
    )

    backend: str = Field(
        default="filesystem",
        alias="BACKEND",
        description="The loader backend to use. Acts as the discriminator.",
    )

    # Polymorphic provider configuration
    provider: Annotated[
        Union[FileSystemLoaderSettings],  # Future: Add MongoSettings here
        Field(discriminator="backend"),
    ] = Field(
        default_factory=FileSystemLoaderSettings,
        alias="PROVIDER",
        description="Specific configuration for the selected loader.",
    )

    renderer: Literal["jinja2"] = Field(
        default="jinja2",
        alias="RENDERER",
        description="The template engine to use for rendering.",
    )
