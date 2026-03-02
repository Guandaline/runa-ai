# src/nala/athomic/context/resolvers.py
from typing import Any, Dict, Protocol, Union, runtime_checkable

from nala.athomic.observability import get_logger

from .exceptions import ContextKeyResolutionError

logger = get_logger(__name__)


@runtime_checkable
class ContextualPayloadProtocol(Protocol):
    """
    Defines the structural contract for objects that carry context and data.

    This Protocol allows the Context module to inspect Message objects from the
    Messaging module (or Requests from HTTP module) without creating circular
    dependencies. It relies on Duck Typing.
    """

    headers: Dict[str, Any]
    payload: Union[Dict[str, Any], Any]


class ContextKeyResolvers:
    """
    Centralized repository of strategy methods for extracting unique business keys.

    This class serves as a bridge between raw business objects (Messages, Dicts, DTOs)
    and the Idempotency/Locking mechanisms. It focuses solely on 'Extraction', leaving
    'Construction' (prefixing, tenancy) to the ContextKeyGenerator.
    """

    @staticmethod
    def _extract_from_headers(target: ContextualPayloadProtocol) -> str:
        """Extract transaction_id from headers."""
        if tx_id := target.headers.get("transaction_id"):
            return str(tx_id).strip()
        return ""

    @staticmethod
    def _extract_from_dict_payload(payload: dict) -> str:
        """Extract transaction_id or id from dict payload."""
        if tx_id := payload.get("transaction_id"):
            return str(tx_id).strip()
        if entity_id := payload.get("id"):
            return str(entity_id).strip()
        return ""

    @staticmethod
    def _extract_from_object_payload(payload: Any) -> str:
        """Extract transaction_id or id from object payload."""
        if hasattr(payload, "transaction_id"):
            val = getattr(payload, "transaction_id")
            return str(val).strip() if val is not None else ""
        if hasattr(payload, "id"):
            val = getattr(payload, "id")
            return str(val).strip() if val is not None else ""
        return ""

    @staticmethod
    def _extract_from_contextual_protocol(target: ContextualPayloadProtocol) -> str:
        """Extract ID from ContextualPayloadProtocol objects."""
        # Priority A: Headers (Metadata)
        if result := ContextKeyResolvers._extract_from_headers(target):
            return result

        # Priority B: Payload (Content)
        payload = target.payload
        if isinstance(payload, dict):
            return ContextKeyResolvers._extract_from_dict_payload(payload)
        else:
            return ContextKeyResolvers._extract_from_object_payload(payload)

    @staticmethod
    def _extract_from_dict(target: dict) -> str:
        """Extract transaction_id or id from dictionary."""
        if tx_id := target.get("transaction_id"):
            return str(tx_id).strip()
        if entity_id := target.get("id"):
            return str(entity_id).strip()
        return ""

    @staticmethod
    def _extract_from_object_attributes(target: Any) -> str:
        """Extract transaction_id or id from object attributes."""
        if hasattr(target, "transaction_id"):
            val = getattr(target, "transaction_id") or ""
            return str(val).strip()
        if hasattr(target, "id"):
            val = getattr(target, "id") or ""
            return str(val).strip()
        return ""

    @staticmethod
    def from_transaction_id(obj: Any, *args, required: bool = False, **kwargs) -> str:
        """
        Smart resolver that attempts to extract a standard 'transaction_id' or 'id'.

        It scans the object using the following priority:
        1. Headers['transaction_id'] (Standard propagation for Messages/Requests)
        2. Payload['transaction_id'] (Business body)
        3. Payload['id'] (Fallback to entity ID)
        4. Dict keys (if obj is a raw dict)
        5. Object attributes (if obj is a Pydantic model or dataclass)

        Args:
            obj: The target object (usually the first argument of the decorated function).

        Returns:
            str: The resolved ID or an empty string if not found.
        """
        target = obj
        result = ""

        # 1. Protocol Check (Message/Request objects)
        if isinstance(target, ContextualPayloadProtocol):
            result = ContextKeyResolvers._extract_from_contextual_protocol(target)

        # 2. Dictionary Check (Raw inputs)
        if not result and isinstance(target, dict):
            result = ContextKeyResolvers._extract_from_dict(target)

        # 3. Attribute Check (Generic Objects/DTOs)
        if not result:
            result = ContextKeyResolvers._extract_from_object_attributes(target)

        if not result:
            msg = f"ContextKeyResolvers: Could not resolve ID from {type(target).__name__}."
            if required:
                raise ContextKeyResolutionError(msg)
            logger.warning(
                f"{msg} Idempotency mechanism might fail or fallback to default."
            )

        return result

    @staticmethod
    def from_attribute(attr_name: str, required: bool = False):
        """
        Factory method to create a specific attribute resolver.

        Useful when the unique key is not 'id' or 'transaction_id', but something
        domain-specific like 'order_number' or 'email'.

        Usage:
            @idempotent(key=ContextKeyResolvers.from_attribute("order_number"))
        """

        def _resolver(obj: Any, *args, **kwargs) -> str:
            # Handle Message-like objects unwrapping
            if isinstance(obj, ContextualPayloadProtocol):
                target = obj.payload
            else:
                target = obj

            result = ""
            # Handle Dicts
            if isinstance(target, dict):
                result = str(target.get(attr_name, "")).strip()
            # Handle Objects
            else:
                val = getattr(target, attr_name, "")
                result = str(val).strip() if val is not None else ""

            if not result and required:
                raise ContextKeyResolutionError(
                    f"Required attribute '{attr_name}' not found in {type(target).__name__}"
                )

            return result

        return _resolver
