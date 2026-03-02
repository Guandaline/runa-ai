# src/nala/athomic/prompts/render/jinja_renderer.py
from typing import Any, Dict

import jinja2
from jinja2 import BaseLoader, Environment
from jinja2 import TemplateSyntaxError as JinjaSyntaxError

from nala.athomic.observability import get_logger

from ...exceptions import RenderError, TemplateSyntaxError
from ...types import PromptTemplate
from ..protocol import PromptRendererProtocol

logger = get_logger(__name__)


class JinjaPromptRenderer(PromptRendererProtocol):
    """
    Concrete implementation of PromptRendererProtocol using Jinja2.

    This renderer allows for logic-heavy prompts (loops, conditionals) which are
    essential for advanced Agentic patterns and Chain-of-Thought reasoning.
    """

    def __init__(self) -> None:
        """
        Initializes the Jinja2 environment.
        We use a stateless loader since templates are passed as strings.
        """
        self._env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # nosec B701 - Generating text/markdown, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,  # Fail fast if a variable is missing
        )

    def render(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        """
        Interpolates the variables into the prompt template.

        Args:
            template: The DTO containing the raw template string.
            variables: The context dictionary to inject.

        Returns:
            str: The rendered string.

        Raises:
            TemplateSyntaxError: If the raw template is invalid.
            RenderError: If rendering fails (e.g., missing variable).
        """
        try:
            # compile string into a Template object
            jinja_template = self._env.from_string(template.template)

            # render with context
            return jinja_template.render(**variables)

        except JinjaSyntaxError as e:
            logger.error(f"Jinja2 syntax error in prompt '{template.name}': {e}")
            raise TemplateSyntaxError(template.name, str(e)) from e

        except jinja2.UndefinedError as e:
            logger.error(f"Missing variable for prompt '{template.name}': {e}")
            raise RenderError(
                f"Rendering failed for '{template.name}': Missing required variable. {e}"
            ) from e

        except Exception as e:
            logger.exception(f"Unexpected error rendering prompt '{template.name}'.")
            raise RenderError(
                f"Unexpected error rendering '{template.name}': {e}"
            ) from e
