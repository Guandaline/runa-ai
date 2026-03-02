from typing import Dict, List, Optional

import tiktoken

from nala.athomic.ai.context.policies import TokenLimitPolicy
from nala.athomic.ai.context.registry import ModelContextRegistry
from nala.athomic.ai.schemas.tokens import TokenBudget
from nala.athomic.config.schemas.ai.context.context_settings import AIContextSettings
from nala.athomic.observability import get_logger
from nala.athomic.services.base import BaseService

logger = get_logger(__name__)


class TokenService(BaseService):
    """
    Domain service for token operations.
    Leverages Registry for physical limits and Policies for effective limits.
    """

    def __init__(
        self,
        settings: AIContextSettings,
        registry: ModelContextRegistry,
        policies: Optional[List[TokenLimitPolicy]] = None,
    ):
        super().__init__(service_name="token_service")
        self.settings = settings
        self.registry = registry
        self.policies = policies or []
        self._encoders: Dict[str, tiktoken.Encoding] = {}

    async def _connect(self) -> None:
        logger.debug("Initializing TokenService encoders...")
        try:
            self._get_encoder(self.settings.default_encoding)
        except Exception as e:
            logger.warning(f"Failed to pre-load default encoder: {e}")
        await self.set_ready()

    def count_tokens(self, text: str, encoding_name: str) -> int:
        if not text:
            return 0
        encoder = self._get_encoder(encoding_name)
        try:
            return len(encoder.encode(text))
        except Exception as e:
            logger.error(f"Tokenization failed: {e}. Fallback estimation.")
            return len(text) // 4

    def calculate_budget(
        self,
        model_name: str,
        system_prompt: str,
        user_query: str,
        max_output_tokens: int = 1024,
    ) -> TokenBudget:
        """
        Calculates token budget applying all active policies.
        """
        # 1. Physical Limit (Hardware/Provider capability)
        limit, encoding_name = self.registry.resolve(
            model_name=model_name,
            default_limit=self.settings.default_model_limit,
            default_encoding=self.settings.default_encoding,
        )

        # 2. Effective Limit (Business Policy application)
        effective_limit = limit
        for policy in self.policies:
            effective_limit = policy.apply(effective_limit, model_name)

        # 3. Budgeting Logic
        sys_tokens = self.count_tokens(system_prompt, encoding_name)
        query_tokens = self.count_tokens(user_query, encoding_name)

        safe_limit = int(effective_limit * (1.0 - self.settings.default_safety_margin))
        used_tokens = sys_tokens + query_tokens + max_output_tokens
        available = max(0, safe_limit - used_tokens)

        utilization = used_tokens / safe_limit if safe_limit > 0 else 1.0

        return TokenBudget(
            model_limit=limit,  # We report the physical limit
            effective_limit=effective_limit,  # And implicitly handle the effective one
            system_prompt_tokens=sys_tokens,
            input_tokens=query_tokens,
            reserved_output_tokens=max_output_tokens,
            available_context_tokens=available,
            utilization_ratio=utilization,
        )

    def _get_encoder(self, encoding_name: str) -> tiktoken.Encoding:
        if encoding_name not in self._encoders:
            try:
                self._encoders[encoding_name] = tiktoken.get_encoding(encoding_name)
            except ValueError:
                self._encoders[encoding_name] = tiktoken.get_encoding("cl100k_base")
        return self._encoders[encoding_name]
