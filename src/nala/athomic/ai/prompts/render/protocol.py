from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class PromptRendererProtocol(Protocol):
    """
    Defines the contract for a Prompt Rendering Engine.

    Implementations (e.g., Jinja2Renderer) are responsible for taking a
    raw template string and substituting variables to produce the final text.
    """

    def render(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Renders the template string using the provided variables.

        Args:
            template_content: The raw string containing placeholders/logic.
            variables: A dictionary of values to inject into the template.

        Returns:
            str: The final processed string.

        Raises:
            PromptValidationError: If rendering fails (e.g., syntax error, missing keys).
        """
        ...
