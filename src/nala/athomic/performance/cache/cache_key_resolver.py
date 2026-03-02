# src/nala/athomic/performance/cache/key_generator.py
import asyncio
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from nala.athomic.performance.cache.protocol import ContextualKeyResolverType


def _default_arg_serializer(obj: Any) -> str:
    """
    Fallback serializer for non-JSON-serializable function arguments (e.g., objects, custom classes).
    This ensures a stable, hashable representation is created for any input type.
    """
    try:
        return repr(obj)
    except Exception:
        # Returns a generic string for types that fail repr
        return f"<unserializable type: {type(obj).__name__}>"


class CacheKeyGenerator:
    """
    Stateless utility class responsible for generating and resolving logical
    and deterministic cache keys used by the caching decorators.

    It handles serialization, hashing, and resolution of dynamic, contextual keys.
    """

    @staticmethod
    def for_function(
        func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> str:
        """
        Generates a logical and deterministic cache key for a function and its arguments.
        The format is: 'function_qualified_name:arguments_hash'.

        This method guarantees that the same inputs always result in the same key.
        """
        function_name = getattr(func, "__qualname__", str(func))

        try:
            # Canonically serialize arguments to create a stable hash:
            # 1. Sort kwargs to ensure stable serialization regardless of Python's insertion order.
            # 2. Use a custom default serializer for non-standard types.
            kwargs_tuple = tuple(sorted(kwargs.items()))
            combined_args = (args, kwargs_tuple)
            serialized_args = json.dumps(
                combined_args, sort_keys=True, default=_default_arg_serializer
            )
            # Hash the serialized arguments to create a compact, safe key component
            hashed_args = hashlib.sha256(serialized_args.encode("utf-8")).hexdigest()
        except Exception:
            # Fallback in case of critical serialization failure
            hashed_args = "hashing_error"

        # Return only the logical part of the key
        return f"{function_name}:{hashed_args}"

    @staticmethod
    async def _contextual_key_resolver(
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        key_resolver: Optional[ContextualKeyResolverType] = None,
    ) -> List[str]:
        """
        Internal method to execute a custom key resolution function (callable)
        or return a fixed string/list if provided.
        """

        if callable(key_resolver):
            # If the resolver is async, await it; otherwise, call it directly
            resolved = (
                await key_resolver(*args, **kwargs)
                if asyncio.iscoroutinefunction(key_resolver)
                else key_resolver(*args, **kwargs)
            )
            # Normalize single string returns into a list
            return [resolved] if isinstance(resolved, str) else resolved

        # If a fixed string was passed
        if isinstance(key_resolver, str):
            return [key_resolver]

        # If a list of strings was passed
        if isinstance(key_resolver, list):
            return key_resolver

        return []

    @staticmethod
    async def resolve_keys(
        func: Callable,
        args: Tuple,
        kwargs: Dict,
        key_resolver: Optional[ContextualKeyResolverType] = None,
        key_prefix: Optional[str] = None,
    ) -> List[str]:
        """
        Resolves the final cache keys to be used for a function call.
        It prioritizes custom contextual resolution over automatic key generation.

        Args:
            func: The decorated function.
            args: Positional arguments passed to the function.
            kwargs: Keyword arguments passed to the function.
            key_resolver: Custom function, string, or list to generate keys.
            key_prefix: A static string prefix to apply to the automatically generated key.

        Returns:
            List[str]: A list of cache keys. Returns an empty list on failure.
        """
        from nala.athomic.observability.log import (
            get_logger,
        )

        logger = get_logger(__name__)

        try:
            # 1. Use custom resolver if provided (e.g., based on tenant_id, user_id)
            if key_resolver is not None:
                return await CacheKeyGenerator._contextual_key_resolver(
                    args, kwargs, key_resolver=key_resolver
                )

            # 2. Fallback to generating a key based on function and arguments
            base_key = CacheKeyGenerator.for_function(func, args, kwargs)

            if key_prefix:
                return [f"{key_prefix}:{base_key}"]

            return [base_key]

        except Exception as e:
            logger.exception(f"Error resolving keys for function {func.__name__}: {e}")
            return []
