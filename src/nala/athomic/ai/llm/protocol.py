# src/nala/athomic/ai/llm/protocol.py
from typing import (
    Any,
    AsyncIterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

from pydantic import BaseModel

from nala.athomic.ai.schemas.llms import LLMResponseChunk

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """
    Protocol defining the contract for Large Language Model (LLM) interactions.
    Focused on text generation and structured data extraction.
    """

    async def generate_content(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generates unstructured text content based on a given prompt.
        """
        ...

    async def stream_content(
        self,
        prompt: Optional[str] = None,
        system_message: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[LLMResponseChunk]:
        """
        Generates unstructured text content incrementally as an asynchronous stream.

        This method is critical for low-latency user experiences (UX).

        Args:
            prompt: The user input text.
            system_message: Optional system instruction.
            **kwargs: Additional generation parameters.

        Returns:
            An asynchronous iterator yielding LLMResponseChunk objects.
        """
        ...

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> T:
        """
        Generates structured data conforming to a specific Pydantic schema.
        """
        ...
