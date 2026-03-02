from enum import Enum
from functools import lru_cache
from typing import final

from nala.athomic.config import get_settings

app_settings = get_settings()


class AppEnvironment(str, Enum):
    """Enumeration representing the possible application environments.

    Inherits from `str` to allow direct comparison with string values, such as
    those retrieved from configuration settings.

    Attributes:
        PRODUCTION: The live, external production environment.
        STAGING: A near-production environment for final testing.
        DEVELOPMENT: A local or shared environment used during active development.
        TESTING: A dedicated environment for running automated tests.
        DEFAULT: The fallback environment if none is explicitly configured.
    """

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEFAULT = "default"


@final
@lru_cache(maxsize=1)
def get_current_environment() -> AppEnvironment:
    """Retrieves the current application environment from global settings.

    The result is cached using `lru_cache` to ensure the configuration is read
    only once during the application's lifecycle, improving performance.

    Returns:
        AppEnvironment: The current, resolved application environment enum member.
    """
    env_str = app_settings.env.lower()
    return AppEnvironment(env_str)


@final
def is_production() -> bool:
    """Checks if the current application environment is set to 'production'.

    Returns:
        bool: True if the environment matches AppEnvironment.PRODUCTION, False otherwise.
    """
    return get_current_environment() == AppEnvironment.PRODUCTION
