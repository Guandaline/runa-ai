# src/nala/athomic/prompts/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class PromptError(AthomicError):
    """Base exception for all errors within the Prompts module."""

    pass


class PromptNotFoundError(PromptError):
    """
    Raised when a prompt definition (directory) or a specific version (file)
    cannot be found in the storage backend.
    """

    pass


class PromptValidationError(PromptError):
    """
    Raised when a prompt template fails validation.
    Examples:
    - Missing required input variables during rendering.
    - Malformed YAML structure.
    - Invalid Jinja2 syntax.
    """

    pass


class PromptLoaderError(PromptError):
    """
    Raised for generic I/O errors during the loading process
    (e.g., file permission denied, database connection failed).
    """

    pass


class RenderError(PromptError):
    """
    Raised when the rendering process fails (e.g., missing variable context).
    """

    pass


class TemplateSyntaxError(PromptError):
    """
    Raised when the raw template string contains invalid syntax (e.g., invalid Jinja2 tags).
    """

    def __init__(self, prompt_name: str, details: str):
        self.prompt_name = prompt_name
        super().__init__(f"Syntax error in prompt '{prompt_name}': {details}")
