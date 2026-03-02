from pathlib import Path
from typing import List

from loguru import logger


def resolve_settings_files(raw_paths_str: str) -> List[Path]:
    """
    Parses a comma-separated string of file paths and returns a
    list of Path objects for files that exist.

    Resolves relative paths from the current working directory (CWD).

    Args:
        raw_paths_str: A string containing one or more file paths,
                       separated by commas.

    Returns:
        A list containing resolved and absolute Path objects for each
        file found and existing. Files not found are logged as warnings
        and omitted from the list.
    """
    settings_files: List[Path] = []
    if not raw_paths_str or not isinstance(raw_paths_str, str):
        logger.warning("Received invalid or empty input for settings file paths.")
        return settings_files

    # Split the string, remove extra spaces, and ignore empty parts
    potential_paths = [p.strip() for p in raw_paths_str.split(",") if p.strip()]
    logger.debug(f"Potential settings file paths to check: {potential_paths}")

    for part in potential_paths:
        try:
            # Path.resolve() correctly handles absolute paths
            # and resolves relative ones from Path.cwd()
            resolved_path = Path(part).resolve()
            logger.debug(f"Checking resolved path: {resolved_path}")

            # Check if it is actually an existing file
            if resolved_path.is_file():
                settings_files.append(resolved_path)
                logger.info(f"Found valid settings file: {resolved_path}")
            else:
                logger.warning(
                    f"Settings file path does not exist or is not a file: {resolved_path} (from input '{part}')"
                )

        except Exception as e:
            # Catch errors during resolution or file checking
            logger.warning(f"Could not process path '{part}'. Error: {e}")

    if not settings_files:
        logger.warning(
            f"No valid settings files were found from input string: '{raw_paths_str}'"
        )

    return settings_files
