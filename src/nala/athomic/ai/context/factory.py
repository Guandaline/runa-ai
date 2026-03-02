from typing import List, Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.context.context_settings import AIContextSettings
from nala.athomic.observability import get_logger

from .manager import TokenService
from .policies import TierBasedLimitPolicy, TokenLimitPolicy
from .registry import ModelContextRegistry

logger = get_logger(__name__)


class TokenServiceFactory:
    """
    Factory that assembles the TokenService, Registry, and default Policies.
    """

    @classmethod
    def create(cls, settings: Optional[AIContextSettings] = None) -> TokenService:
        if settings is None:
            app_settings = get_settings()
            if hasattr(app_settings.ai, "context") and app_settings.ai.context:
                settings = app_settings.ai.context
            else:
                settings = AIContextSettings()

        # 1. Registry
        registry = ModelContextRegistry()
        for rule in settings.model_rules:
            registry.register(name=rule.pattern, item_instance=rule)

        # 2. Default Policies (Example)
        # In a real scenario, we might load these tier limits from settings.toml too
        default_policies: List[TokenLimitPolicy] = [
            TierBasedLimitPolicy(
                tier_limits={"free": 4096, "pro": 32000, "enterprise": 200000}
            )
        ]

        # 3. Service Injection
        return TokenService(
            settings=settings, registry=registry, policies=default_policies
        )
