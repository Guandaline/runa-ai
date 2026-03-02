import re
from typing import Tuple

from nala.athomic.base.instance_registry import BaseInstanceRegistry
from nala.athomic.config.schemas.ai.context.context_settings import ModelRule
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class ModelContextRegistry(BaseInstanceRegistry[ModelRule]):
    """
    Registry for managing Context Window Rules.

    Inherits from BaseInstanceRegistry to leverage standard instance management.
    It stores `ModelRule` objects and provides a semantic `resolve` method
    to find the matching rule for a given model name using Regex.
    """

    def resolve(
        self, model_name: str, default_limit: int, default_encoding: str
    ) -> Tuple[int, str]:
        """
        Resolves the context limit and encoding for a given model name by iterating
        through registered rules.

        Args:
            model_name: The identifier of the model (e.g., "gpt-4-turbo").
            default_limit: Fallback limit if no rule matches.
            default_encoding: Fallback encoding if no rule matches.

        Returns:
            Tuple[int, str]: (context_limit, encoding_name)
        """
        if not model_name:
            return default_limit, default_encoding

        # Iterate over all registered rules (Insertion order is preserved)
        for rule in self.all().values():
            if re.search(rule.pattern, model_name, re.IGNORECASE):
                logger.debug(
                    f"Model '{model_name}' matched rule pattern '{rule.pattern}' "
                    f"(Limit: {rule.context_window})"
                )
                return rule.context_window, rule.encoding_name

        logger.debug(
            f"No context rule found for '{model_name}'. "
            f"Using defaults ({default_limit}, {default_encoding})."
        )
        return default_limit, default_encoding
