# src/nala/athomic/ai/cognitive/providers/llm.py
from typing import Optional

from nala.athomic.ai.cognitive.base import CognitiveBaseService
from nala.athomic.ai.cognitive.exceptions import IntentClassificationError
from nala.athomic.ai.llm.protocol import LLMProviderProtocol
from nala.athomic.ai.prompts.service import PromptService
from nala.athomic.ai.schemas.cognitive import IntentClassification
from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class LLMCognitiveService(CognitiveBaseService):
    """
    Concrete implementation of the Cognitive Service using an LLM backend.
    """

    def __init__(
        self,
        llm: LLMProviderProtocol,
        prompt_service: PromptService,
        settings: CognitiveSettings,
    ):
        # Initialize the Base Service with a descriptive name
        super().__init__(service_name="cognitive_service_llm", settings=settings)
        self._llm = llm
        self._prompts = prompt_service

    async def _connect(self) -> None:
        """Lifecycle hook: Validate dependencies."""
        logger.debug("Connecting LLMCognitiveService dependencies...")
        if hasattr(self._llm, "wait_ready"):
            await self._llm.wait_ready()
        await self.set_ready()

    async def _classify_impl(
        self, query: str, history_context: Optional[str]
    ) -> IntentClassification:
        """
        Executes the LLM structured generation.
        """
        prompt = self._prompts.render(
            name=self.settings.default_prompt_template,
            variables={
                "query": query,
                "history": history_context or "No history available.",
            },
        )

        try:
            return await self._llm.generate_structured(
                prompt=prompt,
                response_model=IntentClassification,
                temperature=0.0,
            )
        except Exception as e:
            raise IntentClassificationError(f"LLM Classification failed: {e}") from e
