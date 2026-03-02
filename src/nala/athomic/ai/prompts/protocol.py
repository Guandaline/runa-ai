# src/nala/athomic/ai/prompts/protocol.py
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .types import PromptTemplate


@runtime_checkable
class PromptSourceProtocol(Protocol):
    """Defines the contract for retrieving raw prompt templates.

    Implementations of this protocol abstract the underlying storage mechanism
    (Filesystem, S3, Database, Git) used to fetch template strings.
    """

    async def get_template(
        self, name: str, version: Optional[str] = None
    ) -> PromptTemplate:
        """Retrieves a prompt template by name and optional version.

        Args:
            name: The logical name of the prompt.
            version: The specific version to retrieve. If None, should return
                     the latest or default version.

        Returns:
            PromptTemplate: The loaded template object.

        Raises:
            PromptNotFoundError: If the template cannot be found.
        """
        ...


@runtime_checkable
class PromptRendererProtocol(Protocol):
    """Defines the contract for interpolating variables into templates.

    Implementations (e.g., Jinja2Renderer) handle the logic of replacing
    placeholders with actual values.
    """

    def render(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        """Renders a template with the provided context variables.

        Args:
            template: The PromptTemplate object containing the raw string.
            variables: A dictionary of values to inject into the template.

        Returns:
            str: The final, interpolated prompt string.

        Raises:
            RenderError: If interpolation fails (e.g., missing variable, syntax error).
        """
        ...
