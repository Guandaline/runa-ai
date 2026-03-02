# src/nala/athomic/ai/cognitive/protocol.py
from typing import Optional, Protocol, runtime_checkable

from nala.athomic.ai.schemas.cognitive import IntentClassification


@runtime_checkable
class CognitiveProtocol(Protocol):
    """
    Defines the contract for Cognitive Providers (Intent Understanding).

    Providers are responsible for the actual execution of intent classification logic,
    whether via LLMs, Machine Learning models, or Heuristics.
    """

    async def classify(
        self, query: str, history_context: Optional[str] = None
    ) -> IntentClassification:
        """
        Analyzes the user query to determine intent.

        Args:
            query: The raw user input.
            history_context: Optional conversation context.

        Returns:
            IntentClassification: The structured classification result.
        """
        ...
