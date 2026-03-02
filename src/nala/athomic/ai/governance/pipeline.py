import logging
from dataclasses import dataclass, field
from typing import Any, List

from nala.athomic.ai.governance.exceptions import (
    QuotaExceededError,
    SecurityPolicyViolationError,
)
from nala.athomic.ai.governance.guards.base import BaseInputGuard, BaseOutputGuard
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config.schemas.ai.governance.governance_settings import (
    PipelineSettings,
)

logger = logging.getLogger(__name__)


class MultipleSecurityViolationsError(SecurityPolicyViolationError):
    """
    Raised when multiple guards fail during the input validation phase
    and 'fail_fast' is disabled.
    """

    def __init__(self, violations: List[str]):
        self.violations = violations
        msg = (
            f"Multiple security policy violations detected ({len(violations)}): "
            f"{'; '.join(violations)}"
        )
        super().__init__(msg)


@dataclass(frozen=True)
class GuardPipeline:
    """
    Encapsulates the AI Governance execution chain with configurable behavior.

    Attributes:
        input_guards: List of validators to run before LLM execution.
        output_guards: List of sanitizers to run after LLM execution.
        settings: Configuration controlling execution flow (timeouts, fail strategies).
    """

    input_guards: List[BaseInputGuard] = field(default_factory=list)
    output_guards: List[BaseOutputGuard] = field(default_factory=list)
    settings: PipelineSettings = field(default_factory=PipelineSettings)

    @property
    def has_input_guards(self) -> bool:
        """Returns True if there are active input guards."""
        return bool(self.input_guards)

    @property
    def has_output_guards(self) -> bool:
        """Returns True if there are active output guards."""
        return bool(self.output_guards)

    async def validate_input(self, prompt: str, **context: Any) -> None:
        """
        Executes all configured input guards.

        Behavior depends on `settings.fail_fast`:
        - True: Raises the exception immediately upon the first violation.
        - False: Executes all guards, collects all violations, and raises
                 MultipleSecurityViolationsError at the end.

        Note: `QuotaExceededError` (Rate Limiting) always raises immediately,
        as it signifies a hard infrastructure limit.
        """
        if not self.input_guards:
            return

        logger.debug(
            f"Executing {len(self.input_guards)} input guards (Fail Fast: {self.settings.fail_fast})."
        )

        violations: List[str] = []

        for guard in self.input_guards:
            try:
                # The check method handles 'enabled' state internally
                await guard.check(prompt, **context)

            except QuotaExceededError as e:
                # Rate Limits are critical infrastructure blocks, fail immediately
                logger.warning(f"Guard '{guard.policy_name}' blocked request: {e}")
                raise e

            except SecurityPolicyViolationError as e:
                if self.settings.fail_fast:
                    logger.warning(f"Guard '{guard.policy_name}' blocked request: {e}")
                    raise e

                # Collect violation and continue
                logger.info(
                    f"Guard '{guard.policy_name}' violation detected (collecting): {e}"
                )
                violations.append(f"[{guard.policy_name}] {str(e)}")

        if violations:
            raise MultipleSecurityViolationsError(violations)

    async def process_output(
        self, response: LLMResponse, **context: Any
    ) -> LLMResponse:
        """
        Executes all configured output guards sequentially (Pipeline pattern).
        Each guard receives the output of the previous one.

        Behavior depends on `settings.continue_on_output_error`:
        - True: If a guard crashes (Exception), log it and pass the previous output to the next guard.
        - False: Raises the exception immediately, aborting the response.
        """
        if not self.output_guards:
            return response

        current_response = response

        logger.debug(f"Executing {len(self.output_guards)} output governance guards.")

        for guard in self.output_guards:
            try:
                # The check_and_process method handles 'enabled' state internally
                current_response = await guard.check_and_process(
                    current_response, **context
                )
            except Exception as e:
                logger.error(
                    f"Output guard '{guard.policy_name}' failed unexpectedly: {e}",
                    exc_info=True,
                )

                if not self.settings.continue_on_output_error:
                    raise SecurityPolicyViolationError(
                        f"Output validation failed at '{guard.policy_name}': {e}"
                    ) from e

                # If resilient, log warning and continue with the last valid response state
                logger.warning(
                    f"Skipping failed output guard '{guard.policy_name}' and continuing."
                )

        return current_response
