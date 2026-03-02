# src/nala/athomic/performance/cache/handlers/invalidation_handler.py
import asyncio
from typing import Callable, Dict, Optional, Tuple

from nala.athomic.observability.log import get_logger

from ..cache_key_resolver import CacheKeyGenerator
from ..protocol import CacheProtocol, ContextualKeyResolverType


class InvalidationHandler:
    """
    Orchestrates the cache invalidation logic for a decorated function call.

    This class is responsible for resolving the appropriate cache keys
    based on function arguments and context, and concurrently deleting them.
    """

    def __init__(
        self,
        func: Callable,
        args: Tuple,
        kwargs: Dict,
        provider: CacheProtocol,
        key_resolver: Optional[ContextualKeyResolverType],
        key_prefix: Optional[str] = None,
    ):
        """
        Initializes the handler with the context necessary for key resolution
        and deletion.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.key_prefix = key_prefix
        self.key_resolver = key_resolver
        self.provider = provider
        self.logger = get_logger(self.__class__.__name__)

    async def invalidate(self) -> None:
        """
        Resolves the target keys using the configured resolver and concurrently
        deletes them from the cache provider.

        The operation handles exceptions but ensures the deletion attempt is made.
        """
        # 1. Resolve Keys: Delegates complex logic (hashing/context) to the generator
        keys_to_invalidate = await CacheKeyGenerator.resolve_keys(
            func=self.func,
            args=self.args,
            kwargs=self.kwargs,
            key_resolver=self.key_resolver,
            key_prefix=self.key_prefix,
        )

        if not keys_to_invalidate:
            return

        try:
            # 2. Concurrency: Create delete tasks for all resolved keys
            delete_tasks = [self.provider.delete(key) for key in keys_to_invalidate]

            # 3. Execution: Run all delete operations concurrently
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
                self.logger.debug(
                    f"Cache invalidated for keys: {keys_to_invalidate} after execution of {self.func.__name__}"
                )
        except Exception as e:
            # Failure is logged but not re-raised to prevent cache failure from
            # crashing the main application flow (security/resilience)
            self.logger.error(
                f"Failed to invalidate cache keys {keys_to_invalidate}: {e}"
            )
