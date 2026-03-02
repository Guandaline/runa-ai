import importlib

import pytest
import pytest_asyncio
import yaml

from nala.athomic.ai.prompts.exceptions import PromptNotFoundError, RenderError
from nala.athomic.ai.prompts.factory import PromptServiceFactory
from nala.athomic.ai.prompts.service import PromptService
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

pytestmark = [pytest.mark.integration, pytest.mark.ai]


@pytest.fixture(scope="function")
def setup_prompt_environment(monkeypatch, tmp_path):
    """
    Sets up a complete test environment:
    1. Creates a temporary directory structure for prompts.
    2. Writes a real YAML prompt file.
    3. Generates a TOML configuration file pointing to this temp directory.
    4. Forces Nala to reload settings using this configuration.
    """
    # 1. Define folder structure
    base_prompts_dir = tmp_path / "prompts"
    base_prompts_dir.mkdir()

    # 2. Create a real prompt file
    prompt_name = "welcome_user"
    prompt_dir = base_prompts_dir / prompt_name
    prompt_dir.mkdir()

    prompt_content = {
        "name": prompt_name,
        "version": "1.0.0",
        "description": "Integration test prompt",
        "input_variables": ["username", "role"],
        "template": "Hello, {{ username }}! Welcome as {{ role }}.",
    }

    with open(prompt_dir / "v1.0.0.yaml", "w") as f:
        yaml.dump(prompt_content, f)

    # 3. Create the TOML configuration file
    toml_content = f"""
    [default]
    app_name = "PromptServiceIntegrationTest"
    log_level = "DEBUG"

    [default.ai]
    enabled = true

    [default.ai.prompts]
    enabled = true
    backend = "filesystem"
    renderer = "jinja2"
    
    [default.ai.prompts.provider]
    backend = "filesystem"
    base_path = "{base_prompts_dir}" 
    """

    settings_file = tmp_path / "test_prompt_settings.toml"
    settings_file.write_text(toml_content, encoding="utf-8")

    # 4. Inject environment variable
    monkeypatch.setenv("NALA_SETTINGS_FILES", str(settings_file))

    # 5. Force settings reload
    get_settings.cache_clear()
    importlib.reload(settings_module)

    # 6. Clear Factory
    PromptServiceFactory.clear()

    yield base_prompts_dir

    # Cleanup
    get_settings.cache_clear()
    PromptServiceFactory.clear()


@pytest_asyncio.fixture
async def prompt_service(setup_prompt_environment) -> PromptService:
    service = PromptServiceFactory.create()
    await service.connect()
    return service


def test_service_e2e_flow(prompt_service: PromptService):
    # Arrange
    variables = {"username": "Maō", "role": "Admin"}

    # Act
    result = prompt_service.render("welcome_user", variables)

    # Assert
    assert "Hello, Maō!" in result
    assert "Welcome as Admin." in result


def test_service_missing_prompt(prompt_service: PromptService):
    with pytest.raises(PromptNotFoundError):
        prompt_service.render("ghost_prompt", {})


def test_service_validation_error(prompt_service: PromptService):
    """
    Verifies that the Service (via Renderer) validates missing variables.
    """
    # Missing 'role' variable
    incomplete_vars = {"username": "Maō"}

    with pytest.raises(RenderError) as exc:
        prompt_service.render("welcome_user", incomplete_vars)

    assert "Missing required variable" in str(exc.value)
    assert "'role' is undefined" in str(exc.value)
