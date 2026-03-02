# src/nala/athomic/config/schemas/prompts/loaders/filesystem_settings.py
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FileSystemLoaderSettings(BaseModel):
    """
    Specific settings for the FileSystem Loader backend.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    backend: Literal["filesystem"] = Field("filesystem", alias="BACKEND")

    base_path: str = Field(
        default="src/nala/resources/prompts",
        alias="BASE_PATH",
        description="Root path where prompt directories are located.",
    )
