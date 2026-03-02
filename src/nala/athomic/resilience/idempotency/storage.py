from typing import Any, Optional

from pydantic import ValidationError

from nala.athomic.config.schemas.resilience.idempotency_configs import (
    IdempotencySettings,
)
from nala.athomic.database.kvstore.factory import KVStoreFactory
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.observability import get_logger

from .models import IdempotencyRecord
from .protocol import IdempotencyStorageProtocol

logger = get_logger(__name__)


class KVIdempotencyStorage(IdempotencyStorageProtocol):
    """
    A concrete implementation of the `IdempotencyStorageProtocol` that uses an
    underlying `KVStoreProtocol` (e.g., Redis) to persist idempotency records.
    """

    def __init__(
        self,
        settings: Optional[IdempotencySettings],
        kv_store: Optional[KVStoreProtocol] = None,
    ):
        """
        Initializes the storage provider.
        """
        self.kv_store = kv_store or KVStoreFactory.create()

    async def get_record(self, key: str) -> Optional[IdempotencyRecord]:
        """
        Retrieves the stored idempotent record.
        It attempts to parse the data into an IdempotencyRecord wrapper.
        """
        try:
            stored_data = await self.kv_store.get(key)
            if stored_data is None:
                return None

            # We expect the data to be wrapped in our Generic Record structure
            return IdempotencyRecord.model_validate(stored_data)

        except ValidationError:
            logger.warning(
                f"Invalid data format found in idempotency storage for key '{key}'. "
                "Treating as a cache miss."
            )
            return None
        except Exception:
            logger.exception(
                f"Failed to get idempotency record for key '{key}'. "
                "Returning None to allow the operation to proceed without guarantees."
            )
            return None

    async def store_record(self, key: str, data: Any, ttl: int) -> None:
        """
        Stores the result of a successful idempotent operation.
        It wraps the raw result in an IdempotencyRecord to handle 'None' returns safely.
        """
        try:
            # Wrap the result to distinguish "None result" from "Key not found"
            record = IdempotencyRecord(result=data)

            # nx=True ensures this operation succeeds only if the key does NOT already exist
            await self.kv_store.set(key, record, ttl=ttl, nx=True)
        except Exception:
            logger.exception(f"Failed to store idempotency record for key '{key}'.")
