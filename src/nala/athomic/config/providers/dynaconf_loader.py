import os
from pathlib import Path
from typing import List, Optional

from dynaconf import Dynaconf
from loguru import logger

from .dynaconf_env import get_path_from_env
from .dynaconf_files import resolve_settings_files

SETTINGS_FILES_ENV_VAR: str = "NALA_SETTINGS_FILES"
DOTENV_PATH_ENV_VAR: str = "NALA_DOTENV_PATH"
ENV_SWITCHER_ENV_VAR: str = "NALA_ENV_FOR_DYNACONF"
ENVVAR_PREFIX: str = "NALA"

DEFAULT_SETTINGS_FILES: str = "settings/settings.toml"
DEFAULT_DOTENV_PATH: str = ".env"
DEFAULT_ENV_SWITCHER: str = "ENV_FOR_DYNACONF"


class DynaconfLoader:
    def __init__(self) -> None:
        logger.debug("DynaconfLoader initialized.")

    def load(self) -> Dynaconf:
        logger.info("Starting configuration loading via Dynaconf...")

        raw_settings_paths: str = os.getenv(
            SETTINGS_FILES_ENV_VAR, DEFAULT_SETTINGS_FILES
        )

        logger.debug(
            f"Raw settings paths from env var '{SETTINGS_FILES_ENV_VAR}': {raw_settings_paths}"
        )
        settings_files: List[Path] = resolve_settings_files(raw_settings_paths)

        if not settings_files:
            logger.error(
                f"No valid settings files found. Check env var '{SETTINGS_FILES_ENV_VAR}' "
                f"(current value: '{os.getenv(SETTINGS_FILES_ENV_VAR)}') or default path '{DEFAULT_SETTINGS_FILES}'. "
                f"Searched pattern: '{raw_settings_paths}'"
            )
            raise RuntimeError("DynaconfLoader: No settings files could be loaded.")

        settings_files_str: List[str] = [str(p) for p in settings_files]
        logger.info(f"Dynaconf - Using settings files: {settings_files_str}")

        dotenv_path: Optional[Path] = get_path_from_env(
            DOTENV_PATH_ENV_VAR, DEFAULT_DOTENV_PATH
        )
        dotenv_path_str: Optional[str] = None
        load_dotenv_flag: bool = False
        if dotenv_path and dotenv_path.is_file():
            dotenv_path_str = str(dotenv_path)
            load_dotenv_flag = True
            logger.info(f"Dynaconf - Using .env file: {dotenv_path_str}")
        else:
            logger.info(
                f"Dynaconf - No .env file found or specified (checked env var '{DOTENV_PATH_ENV_VAR}' "
                f"and default '{DEFAULT_DOTENV_PATH}'). Dotenv loading disabled."
            )

        env_switcher_var_name: str = os.getenv(
            ENV_SWITCHER_ENV_VAR, DEFAULT_ENV_SWITCHER
        )
        current_env: Optional[str] = os.getenv(env_switcher_var_name)
        logger.info(
            f"Dynaconf - Environment switcher var: '{env_switcher_var_name}'. "
            f"Current active environment: '{current_env or 'default'}'"
        )

        logger.debug(
            f"Initializing Dynaconf (prefix: '{ENVVAR_PREFIX}', env_switcher: '{env_switcher_var_name}', merge: True)"
        )
        try:
            settings = Dynaconf(
                envvar_prefix=ENVVAR_PREFIX,
                environments=True,
                settings_files=settings_files_str,
                env_switcher=env_switcher_var_name,
                load_dotenv=load_dotenv_flag,
                dotenv_path=dotenv_path_str,
                merge_enabled=True,
            )
            logger.success("Dynaconf instance created and configuration loaded.")
            return settings

        except Exception as e:
            logger.exception("Dynaconf failed during initialization.")
            raise RuntimeError(
                "DynaconfLoader: Failed to initialize Dynaconf instance."
            ) from e
