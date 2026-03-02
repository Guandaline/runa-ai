# src/nala/athomic/resilience/orchestrator.py
from typing import Any, Awaitable, Callable, Optional

from nala.athomic.resilience.circuit_breaker import CircuitBreakerService
from nala.athomic.resilience.retry import RetryHandler


class ResilienceOrchestrator:
    """
    Orchestrates the execution of an asynchronous function through configured layers of resilience.

    This class enforces the chain of resilience patterns, ensuring that the function:
    1. Is protected by the **Circuit Breaker** (outer layer).
    2. Executes the **Retry** logic (inner layer, wrapped by the Circuit Breaker).
    3. Executes the original function (innermost layer).

    This class is generic and does not depend on HTTP or any specific protocol.

    Attributes:
        retry_handler (Optional[RetryHandler]): The handler responsible for retrying failed calls.
        circuit_breaker (Optional[CircuitBreakerService]): The service managing the circuit's state.
        circuit_breaker_name (Optional[str]): The specific name of the circuit to be enforced.
    """

    def __init__(
        self,
        retry_handler: Optional[RetryHandler] = None,
        circuit_breaker: Optional[CircuitBreakerService] = None,
        circuit_breaker_name: Optional[str] = None,
    ):
        """
        Initializes the ResilienceOrchestrator with its resilience dependencies.

        Args:
            retry_handler (Optional[RetryHandler]): The handler that implements the retry policy.
            circuit_breaker (Optional[CircuitBreakerService]): The service that manages circuit state.
            circuit_breaker_name (Optional[str]): The unique name of the circuit to apply.
        """
        self.retry_handler = retry_handler
        self.circuit_breaker = circuit_breaker
        self.circuit_breaker_name = circuit_breaker_name

    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Executes the provided asynchronous function within the resilience pipeline.

        The execution order is: Circuit Breaker -> (Retry Handler or Direct Call) -> Original Function.

        Args:
            func (Callable[..., Awaitable[Any]]): The original asynchronous function to be executed.
            *args (Any): Positional arguments for the function.
            **kwargs (Any): Keyword arguments for the function.

        Returns:
            Any: The result of the executed function.

        Raises:
            Exception: Propagates exceptions from the Circuit Breaker, Retry Handler, or the original function.
        """

        async def _direct_call() -> Any:
            """Executes the original function without retry logic."""
            return await func(*args, **kwargs)

        async def _retry_call() -> Any:
            """Executes the original function protected by the Retry Handler."""
            # Uses the asynchronous run method of the RetryHandler
            return await self.retry_handler.arun(func, *args, **kwargs)

        # Determine the inner callable (Retry is prioritized if configured)
        final_callable = _retry_call if self.retry_handler else _direct_call

        # Outer layer: Execute protected by the Circuit Breaker
        if self.circuit_breaker and self.circuit_breaker_name:
            return await self.circuit_breaker.execute(
                circuit_name=self.circuit_breaker_name,
                func=final_callable,
            )
        else:
            # Execute without circuit breaker protection
            return await final_callable()
