# src/nala/athomic/prompts/io/protocol.py
from typing import Optional, Protocol, runtime_checkable

from ..types import PromptTemplate


@runtime_checkable
class PromptLoaderProtocol(Protocol):
    """
    Defines the contract for loading prompt definitions (templates) from a storage backend.

    Implementations (e.g., FileSystemPromptLoader, MongoPromptLoader) must
    adhere to this interface to be used by the PromptManager.
    """

    def get(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        """
        Retrieves a specific prompt definition by its unique name and optional version.

        Args:
            name (str): The unique identifier for the prompt (e.g., 'sentiment_analysis').
            version (Optional[str]): The semantic version string (e.g., '1.0.0').
                                     If None, the loader implementation MUST resolve and
                                     return the latest stable version available.

        Returns:
            PromptTemplate: The data object containing the raw template and metadata.

        Raises:
            PromptNotFoundError: If the prompt name or the specific version does not exist.
            PromptLoaderError: If there is an issue accessing the storage backend.
            PromptValidationError: If the stored data is corrupted or invalid.
        """
        ...
