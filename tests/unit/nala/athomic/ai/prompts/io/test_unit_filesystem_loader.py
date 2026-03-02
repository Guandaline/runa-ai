from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml

from nala.athomic.ai.prompts.exceptions import (
    PromptLoaderError,
    PromptNotFoundError,
    PromptValidationError,
)
from nala.athomic.ai.prompts.io.loaders.filesystem import FileSystemPromptLoader
from nala.athomic.config.schemas.ai.prompts.loaders import (
    FileSystemLoaderSettings,
)

# --- Helpers ---


def create_prompt_file(
    base_dir: Path, prompt_name: str, version: str, content: Dict[str, Any]
) -> None:
    """Helper to create a YAML prompt file in the temp directory."""
    prompt_dir = base_dir / prompt_name
    prompt_dir.mkdir(parents=True, exist_ok=True)

    file_path = prompt_dir / f"v{version}.yaml"
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(content, f)


# --- Fixtures ---


@pytest.fixture
def prompts_dir(tmp_path):
    """Creates a temporary root directory for prompts."""
    path = tmp_path / "prompts"
    path.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    return path


@pytest.fixture
def loader(prompts_dir):
    """Initializes the loader pointing to the temp directory."""
    settings = FileSystemLoaderSettings(base_path=str(prompts_dir))
    return FileSystemPromptLoader(settings)


# --- Tests ---


class TestFileSystemPromptLoader:
    def test_get_specific_version_success(self, loader, prompts_dir):
        """Should load a specific version of a prompt correctly."""
        # Arrange
        data = {
            "name": "sentiment",
            "version": "1.0.0",
            "template": "Analyze: {{ text }}",
            "input_variables": ["text"],
        }
        create_prompt_file(prompts_dir, "sentiment", "1.0.0", data)

        # Act
        result = loader.get("sentiment", version="1.0.0")

        # Assert
        assert result.name == "sentiment"
        assert result.version == "1.0.0"
        assert result.template == "Analyze: {{ text }}"

    def test_get_latest_version_resolution(self, loader, prompts_dir):
        """Should resolve the highest semantic version when no version is provided."""
        # Arrange: Create v1.9.0 and v1.10.0
        base_data = {"name": "logic", "template": "...", "input_variables": []}

        create_prompt_file(
            prompts_dir, "logic", "1.9.0", {**base_data, "version": "1.9.0"}
        )
        create_prompt_file(
            prompts_dir, "logic", "1.10.0", {**base_data, "version": "1.10.0"}
        )
        create_prompt_file(
            prompts_dir, "logic", "1.2.0", {**base_data, "version": "1.2.0"}
        )

        # Act
        result = loader.get("logic")  # No version specified

        # Assert
        assert result.version == "1.10.0"

    def test_get_prompt_not_found_directory(self, loader):
        """Should raise PromptNotFoundError if the prompt directory does not exist."""
        with pytest.raises(PromptNotFoundError) as exc:
            loader.get("non_existent_prompt")

        assert "Prompt directory not found" in str(exc.value)

    def test_get_version_not_found(self, loader, prompts_dir):
        """Should raise PromptNotFoundError if the specific version file is missing."""
        # Arrange
        create_prompt_file(
            prompts_dir,
            "sentiment",
            "1.0.0",
            {"name": "s", "version": "1", "template": "", "input_variables": []},
        )

        # Act & Assert
        with pytest.raises(PromptNotFoundError) as exc:
            loader.get("sentiment", version="2.0.0")

        assert "Version '2.0.0' not found" in str(exc.value)

    def test_load_malformed_yaml(self, loader, prompts_dir):
        """Should raise PromptLoaderError if the file contains invalid YAML."""
        # Arrange
        prompt_dir = prompts_dir / "broken"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        with open(prompt_dir / "v1.0.0.yaml", "w") as f:
            f.write("name: : : invalid_yaml_structure")

        # Act & Assert
        with pytest.raises(PromptLoaderError) as exc:
            loader.get("broken", version="1.0.0")

        assert "Corrupted YAML" in str(exc.value)

    def test_load_invalid_schema(self, loader, prompts_dir):
        """Should raise PromptValidationError if YAML is valid but missing required fields."""
        # Arrange: Missing 'template' field
        data = {
            "name": "sentiment",
            "version": "1.0.0",
            # "template": "MISSING",
            "input_variables": [],
        }
        create_prompt_file(prompts_dir, "invalid_schema", "1.0.0", data)

        # Act & Assert
        with pytest.raises(PromptValidationError) as exc:
            loader.get("invalid_schema", version="1.0.0")

        assert "Invalid prompt schema" in str(exc.value)

    def test_base_path_warning(self):
        """Should log a warning and raise PromptLoaderError if initialized with a non-existent path."""
        # Arrange
        bad_settings = FileSystemLoaderSettings(
            base_path="/path/that/does/not/exist/at/all"
        )

        # Act
        with patch(
            "nala.athomic.ai.prompts.io.loaders.filesystem.logger"
        ) as mock_logger:
            # We must expect the error here because the loader raises exception after logging
            with pytest.raises(PromptLoaderError):
                FileSystemPromptLoader(bad_settings)

            # Assert
            mock_logger.warning.assert_called_once()
            args, _ = mock_logger.warning.call_args
            assert "Prompt base path does not exist" in args[0]
