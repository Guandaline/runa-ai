# nala/athomic/config/schemas/base_config.py

from typing import Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

ClientSettingsT = TypeVar("ClientSettingsT")


class ConnectionGroupSettings(BaseModel, Generic[ClientSettingsT]):
    """
    A generic Pydantic model that defines a standardized structure for a group
    of named connection configurations.
    """

    enabled: bool = Field(default=True)
    connections: Dict[str, ClientSettingsT] = Field(default_factory=dict)
    default_connection_name: Optional[str] = Field(default=None)

    def get_default(self) -> Optional[ClientSettingsT]:
        """
        Retrieves the default connection settings based on the
        `default_connection_name`. Returns None if not set or not found.
        """
        if self.default_connection_name:
            return self.connections.get(self.default_connection_name)
        return None
