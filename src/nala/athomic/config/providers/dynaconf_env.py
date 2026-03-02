import os
from pathlib import Path
from typing import Optional

from loguru import logger


def get_path_from_env(
    env_var_name: str, default_relative_path: Optional[str] = None
) -> Optional[Path]:
    """
    Resolves a path (Path) from an environment variable.

    If the environment variable is not set, tries to use a default
    relative path (from the current working directory).

    Args:
        env_var_name: The name of the environment variable to read.
        default_relative_path: Relative path to use if the environment
                               variable is not found.

    Returns:
        An absolute resolved Path object if a valid path is found,
        otherwise, None.
    """
    logger.debug(
        f"Attempting to resolve path from environment variable: '{env_var_name}'"
    )
    path_str = os.getenv(env_var_name)

    resolved_path: Optional[Path] = None

    if path_str:
        # If the environment variable was found
        logger.info(f"Environment variable '{env_var_name}' found: '{path_str}'")
        try:
            # Resolve the path (handles absolute and relative paths from CWD)
            resolved_path = Path(path_str).resolve()
            logger.debug(f"Resolved path from env var: {resolved_path}")
        except Exception as e:
            # Catch potential errors in Path resolution
            logger.warning(
                f"Could not resolve path '{path_str}' from env var '{env_var_name}': {e}"
            )
            resolved_path = None  # Ensure None in case of error

    elif default_relative_path:
        # If the variable was not found, but a default was provided
        logger.warning(
            f"Environment variable '{env_var_name}' not set. "
            f"Attempting fallback relative path: '{default_relative_path}'"
        )
        try:
            # Resolve the relative path from the current working directory (CWD)
            resolved_path = (Path.cwd() / default_relative_path).resolve()
            logger.debug(f"Resolved path from fallback: {resolved_path}")
        except Exception as e:
            logger.warning(
                f"Could not resolve fallback path '{default_relative_path}': {e}"
            )
            resolved_path = None
    else:
        # If the variable was not found and no default is provided
        logger.debug(
            f"Environment variable '{env_var_name}' not set and no fallback provided."
        )
        resolved_path = None

    return resolved_path
