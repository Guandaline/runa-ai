# File: src/nala/athomic/config/settings.py
from functools import lru_cache
from typing import Any, Dict, Optional

from dynaconf import Dynaconf
from loguru import logger
from pydantic import ValidationError

from .providers.dynaconf_loader import DynaconfLoader
from .schemas.app_settings import AppSettings


@lru_cache()
def get_settings() -> AppSettings:
    """Loads, validates, and returns the application settings as a singleton.

    This is the primary entry point for accessing application configuration. It
    uses `@lru_cache` to ensure that the potentially expensive process of loading
    and validating settings from files and environment variables happens only once.

    Returns:
        AppSettings: A validated Pydantic model containing the entire
        application configuration.
    """
    logger.debug("Calling _load_and_validate_settings to get/cache settings.")
    return _load_and_validate_settings()


def _load_and_validate_settings() -> AppSettings:
    """Orchestrates the two-step process of loading and validating settings.

    This function first uses `DynaconfLoader` to load raw configuration data
    from files (e.g., .toml) and environment variables into a dictionary. It then
    passes this dictionary to the `AppSettings` Pydantic model for comprehensive
    validation of structure, types, and required fields.

    Returns:
        AppSettings: The validated settings object if successful.

    Raises:
        RuntimeError: If the `DynaconfLoader` fails to load configuration.
        ValueError: If the loaded configuration fails Pydantic validation.
    """
    logger.debug("Running _load_and_validate_settings")

    logger.info("Loading raw configuration using DynaconfLoader...")
    raw_config_dict: Dict[str, Any] = {}
    dynaconf_instance: Optional[Dynaconf] = None

    try:
        loader = DynaconfLoader()
        dynaconf_instance = loader.load()
        current_env = dynaconf_instance.current_env
        raw_config_dict = dynaconf_instance.as_dict(env=current_env)
        logger.debug(
            f"Raw config dict loaded by Dynaconf for env '{current_env}': {raw_config_dict}"
        )

    except Exception as e:
        logger.exception("Failed to load configuration via DynaconfLoader.")
        raise RuntimeError("Application configuration could not be loaded.") from e

    if not raw_config_dict and dynaconf_instance:
        logger.warning(
            f"Dynaconf loaded successfully but resulting dictionary for env '{dynaconf_instance.current_env}' is empty."
        )
        raw_config_dict = {}

    logger.info("Validating configuration using Pydantic schema (AppSettings)...")

    try:
        dict_to_pass = raw_config_dict.copy()

        logger.debug(f"[Pydantic Check] Keys in dict: {list(dict_to_pass.keys())}")

        validated_settings = AppSettings(**dict_to_pass)
        logger.debug(
            f"Pydantic validation successful. App Name: '{validated_settings.app_name}'"
        )
        logger.success("Configuration loaded and validated successfully!")
        return validated_settings
    except ValidationError as e:
        logger.error(f"Pydantic validation failed! Errors:\n{e}")
        raise ValueError(f"Application configuration validation failed: {e}") from e
    except Exception as e:
        logger.exception("An unexpected error occurred during Pydantic validation.")
        raise ValueError(
            "Application configuration validation failed (Unexpected)."
        ) from e
