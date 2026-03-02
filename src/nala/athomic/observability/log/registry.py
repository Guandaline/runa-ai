from typing import Any, List, Type

from nala.athomic.observability.log.maskers.base_masker import BaseMasker

# Global registry for all maskers
MASKER_REGISTRY: List[Type[BaseMasker]] = []


def register_masker(masker_cls: Type[BaseMasker]) -> Any:
    """Register a new masker class into the global registry."""
    MASKER_REGISTRY.append(masker_cls)
