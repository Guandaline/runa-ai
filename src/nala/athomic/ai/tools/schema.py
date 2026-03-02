# src/nala/athomic/ai/tools/schema.py
import inspect
from typing import Any, Callable, Dict, Type

from pydantic import BaseModel, create_model

DEF_KEYS = "$defs"


class SchemaGenerator:
    """
    Utilities to generate schemas and validation models from Python callables.
    """

    @staticmethod
    def create_arguments_model(func: Callable[..., Any]) -> Type[BaseModel]:
        """
        Creates a dynamic Pydantic model representing the function arguments.
        This model is used for runtime validation and type coercion.
        """
        sig = inspect.signature(func)
        fields = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            annotation = param.annotation
            if annotation == inspect.Parameter.empty:
                annotation = Any

            default = param.default
            if default == inspect.Parameter.empty:
                fields[param_name] = (annotation, ...)
            else:
                fields[param_name] = (annotation, default)

        model_name = f"{func.__name__}Arguments"
        return create_model(model_name, **fields)  # type: ignore

    @staticmethod
    def generate(func: Callable[..., Any]) -> Dict[str, Any]:
        """
        Generates the JSON Schema for the function, including definitions.
        """
        model = SchemaGenerator.create_arguments_model(func)

        # Pydantic V2 uses $defs for Enums and complex types.
        # We must include them so the LLM knows the allowed values.
        schema = model.model_json_schema()

        # Build the final schema structure
        tool_schema = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }

        # If there are definitions (like Enums), include them
        if DEF_KEYS in schema:
            tool_schema[DEF_KEYS] = schema[DEF_KEYS]

        return tool_schema
