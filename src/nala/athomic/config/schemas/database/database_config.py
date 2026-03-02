# src/nala/athomic/config/schemas/database/database_config.py
"""Defines the Pydantic schema for all database-related configurations."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from nala.athomic.config.schemas.base_settings import ConnectionGroupSettings
from nala.athomic.enums.defaults import Defaults

from .kvstore.kvstore_config import KVStoreSettings


class DatabaseSettings(BaseModel):
    """
    Defines the configuration for all database-related services.

    This model aggregates the configurations for different types of data stores,
    including document databases (e.g., MongoDB), key-value stores (e.g., Redis),
    and the database migration engine. It allows for defining multiple named
    connections for each type of store.

    Attributes:
        default_document_connection (str): The name of the default document
            database connection.
        default_kvstore_connection (str): The name of the default key-value
            store connection.
        enabled (Optional[bool]): A master switch for all database features.
        documents (Dict[str, DocumentsSettings]): Named configurations for
            document database connections.
        kvstore (Dict[str, KVStoreSettings]): Named configurations for
            key-value store connections.
        migrations (Optional[MigrationSettings]): Configuration for the
            database migration engine.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: Optional[bool] = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to enable or disable all database features globally.",
    )

    default_kvstore_connection: str = Field(
        default=Defaults.DEFAULT_REDIS_CONNECTION,
        description="The name of the default key-value store connection to use.",
        alias="DEFAULT_KVSTORE_CONNECTION",
    ) 
    
    kvstore: Optional[ConnectionGroupSettings[KVStoreSettings]] = Field(
        default=None,
        alias="KVSTORE",
        description="Configuration for key-value store connections (e.g., Redis).",
    )

