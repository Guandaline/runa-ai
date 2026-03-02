# src/nala/athomic/health/readiness/registry.py
from typing import Dict

from .protocol import ReadinessCheck


class ReadinessRegistry:
    """
    A registry responsible for collecting and orchestrating all application
    readiness checks.

    This acts as a centralized source of truth for determining if the application
    and its core dependencies (databases, message brokers, external services)
    are fully initialized and ready to handle live traffic.
    """

    def __init__(self) -> None:
        """
        Initializes the internal dictionary to store readiness checks, mapped by name.
        """
        self._checks: Dict[str, ReadinessCheck] = {}

    def register(self, check: ReadinessCheck) -> None:
        """
        Registers a new ReadinessCheck implementation with the registry.

        Args:
            check: An instance of a ReadinessCheck protocol implementation.
        """
        self._checks[check.name] = check

    async def run_all(self) -> Dict[str, str]:
        """
        Executes all registered readiness checks asynchronously.

        It respects the `enabled()` status of each check and handles
        exceptions during execution by marking the check as failed.

        Returns:
            Dict[str, str]: A dictionary containing the name of each check
                            and its resulting status: 'ok', 'fail', or 'skipped'.
        """
        result = {}
        for name, check in self._checks.items():
            if not check.enabled():
                result[name] = "skipped"
            else:
                try:
                    result[name] = "ok" if await check.check() else "fail"
                except Exception:
                    result[name] = "fail"
        return result


readiness_registry = ReadinessRegistry()
