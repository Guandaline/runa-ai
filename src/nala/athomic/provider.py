# src/nala/athomic/provider.py
from typing import Optional

from nala.athomic.facade import Athomic
from nala.athomic.observability import get_logger

logger = get_logger("AthomicProvider")

# Global variable to store the single (Singleton) instance
_athomic_instance: Optional[Athomic] = None


def set_athomic_instance(instance: Athomic) -> None:
    """
    Sets the global singleton instance of the Athomic facade.
    This function should be called ONLY ONCE during application startup.
    """
    global _athomic_instance
    if _athomic_instance is not None:
        logger.warning(
            "Athomic instance is being overwritten. This should not happen in production."
        )
    _athomic_instance = instance


def get_athomic_instance() -> Athomic:
    """
    Returns the singleton instance of the Athomic facade that has already been initialized.

    Raises:
        RuntimeError: If the instance has not yet been created and set.
    """
    if _athomic_instance is None:
        raise RuntimeError(
            "Athomic facade has not been initialized. "
            "It must be created and set via set_athomic_instance() during the application lifespan startup."
        )
    return _athomic_instance


def clear_athomic_instance() -> None:
    """For use in tests, to ensure isolation."""
    global _athomic_instance
    _athomic_instance = None
