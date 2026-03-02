import pytest

from nala.athomic.ai.prompts.exceptions import RenderError, TemplateSyntaxError
from nala.athomic.ai.prompts.render import JinjaPromptRenderer
from nala.athomic.ai.prompts.types import PromptTemplate


@pytest.fixture
def renderer():
    return JinjaPromptRenderer()


def create_template(content: str, name: str = "test_prompt") -> PromptTemplate:
    return PromptTemplate(
        name=name,
        version="1.0.0",
        template=content,
        input_variables=[],  # The renderer ignores this list, only Domain uses it
    )


class TestJinjaPromptRenderer:
    def test_render_success_simple_interpolation(self, renderer):
        """Should substitute simple variables correctly."""
        template = create_template("Hello, {{ name }}!")
        variables = {"name": "Maō"}

        result = renderer.render(template, variables)

        assert result == "Hello, Maō!"

    def test_render_success_complex_logic(self, renderer):
        """Should process Jinja2 logic (loops and conditionals)."""
        content = """
        Items:
        {% for item in items %}
        - {{ item }}
        {% endfor %}
        {% if show_footer %}END{% endif %}
        """
        template = create_template(content)
        variables = {"items": ["A", "B"], "show_footer": True}

        result = renderer.render(template, variables)

        # Renderer is configured with trim_blocks=True
        assert "- A" in result
        assert "- B" in result
        assert "END" in result

    def test_render_fail_missing_variable(self, renderer):
        """Should raise RenderError if a required variable is missing."""
        # StrictUndefined is enabled
        template = create_template("Hello, {{ name }}!")
        variables = {}  # Missing 'name'

        with pytest.raises(RenderError) as exc_info:
            renderer.render(template, variables)

        assert "Missing required variable" in str(exc_info.value)

    def test_render_fail_syntax_error(self, renderer):
        """Should raise TemplateSyntaxError if Jinja syntax is invalid."""
        # Broken syntax: {% if %} without condition or endif
        template = create_template("Hello {% if %}")
        variables = {}

        with pytest.raises(TemplateSyntaxError) as exc_info:
            renderer.render(template, variables)

        assert "Syntax error in prompt" in str(exc_info.value)

    def test_render_ignores_extra_variables(self, renderer):
        """Should ignore extra variables not present in the template."""
        template = create_template("Hello, {{ name }}!")
        variables = {"name": "Maō", "extra": "ignored"}

        result = renderer.render(template, variables)

        assert result == "Hello, Maō!"
