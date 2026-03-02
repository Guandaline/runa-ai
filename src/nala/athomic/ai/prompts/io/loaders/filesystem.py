import re
from pathlib import Path
from typing import Optional, Tuple

import yaml
from pydantic import ValidationError

from nala.athomic.config.schemas.ai.prompts.loaders import (
    FileSystemLoaderSettings,
)
from nala.athomic.observability import get_logger

from ...exceptions import PromptLoaderError, PromptNotFoundError, PromptValidationError
from ...types import PromptTemplate
from ..protocol import PromptLoaderProtocol

logger = get_logger(__name__)


class FileSystemPromptLoader(PromptLoaderProtocol):
    """
    Loads prompt definitions from the local filesystem.

    It expects a directory structure organized by prompt name, containing
    versioned YAML files.

    Expected Structure:
    {base_path}/
      ├── sentiment_analysis/
      │   ├── v1.0.0.yaml
      │   └── v1.1.0.yaml
      └── text_summary/
          └── v1.0.0.yaml
    """

    def __init__(self, settings: FileSystemLoaderSettings):
        """
        Initializes the loader with the configured base path.

        Args:
            settings: Specific settings for the FileSystemLoader (contains base_path).
        """
        raw_path = Path(settings.base_path)

        try:
            self.base_path = raw_path.expanduser().resolve()
        except Exception:
            self.base_path = raw_path

        logger.debug(f"Prompt loader base path resolved to: {self.base_path}")

        if not self.base_path.exists():
            logger.warning(
                f"Prompt base path does not exist: {self.base_path}. "
                "Ensure prompts are mounted or created."
            )
            raise PromptLoaderError(f"Prompt base path not found: {self.base_path}")

    def get(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        """
        Retrieves the YAML file for the prompt and converts it into a PromptTemplate.

        If the version is not provided, it scans the directory and resolves the
        highest semantic version.

        Args:
            name: The unique identifier of the prompt (directory name).
            version: The specific version (e.g., '1.0.0'). If None, resolves to latest.

        Returns:
            PromptTemplate: The loaded prompt definition.

        Raises:
            PromptNotFoundError: If the directory or version file is missing.
        """
        prompt_dir = self.base_path / name

        if not prompt_dir.exists() or not prompt_dir.is_dir():
            raise PromptNotFoundError(
                f"Prompt directory not found for '{name}' at {prompt_dir}"
            )

        target_file: Path

        if version:
            # Direct lookup for the requested version
            target_file = prompt_dir / f"v{version}.yaml"
            if not target_file.exists():
                raise PromptNotFoundError(
                    f"Version '{version}' not found for prompt '{name}'"
                )
        else:
            # Resolve the latest version automatically
            target_file = self._resolve_latest_version(prompt_dir)
            if not target_file:
                raise PromptNotFoundError(
                    f"No valid version files (vX.Y.Z.yaml) found for prompt '{name}'"
                )

            logger.debug(f"Resolved latest version for '{name}': {target_file.name}")

        return self._load_file(target_file)

    def _resolve_latest_version(self, directory: Path) -> Optional[Path]:
        """
        Finds the file with the highest semantic version in the directory.
        Example: v1.10.0 ranks higher than v1.9.0.
        """
        files = list(directory.glob("v*.yaml"))
        if not files:
            return None

        # Helper function to extract version tuple: 'v1.2.3.yaml' -> (1, 2, 3)
        def version_key(path: Path) -> Tuple[int, ...]:
            # Extracts numbers after 'v' and before '.yaml'
            match = re.search(r"v(\d+(?:\.\d+)*)", path.name)
            if match:
                try:
                    return tuple(map(int, match.group(1).split(".")))
                except ValueError:
                    pass
            return (0,)  # Fallback for non-compliant filenames

        # Sort descending (highest version first)
        files.sort(key=version_key, reverse=True)

        return files[0]

    def _load_file(self, file_path: Path) -> PromptTemplate:
        """
        Reads the YAML file, validates the schema, and returns the object.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if not content:
                raise PromptValidationError(f"Prompt file is empty: {file_path}")

            # Pydantic validation happens here
            return PromptTemplate(**content)

        except ValidationError as e:
            logger.error(f"Schema validation failed for {file_path}: {e}")
            raise PromptValidationError(
                f"Invalid prompt schema in {file_path.name}: {e}"
            ) from e

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing failed for {file_path}: {e}")
            raise PromptLoaderError(f"Corrupted YAML in {file_path.name}") from e

        except Exception as e:
            logger.error(f"Unexpected error loading prompt {file_path}: {e}")
            raise PromptLoaderError(f"Failed to load prompt {file_path.name}") from e
