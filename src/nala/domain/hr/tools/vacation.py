from typing import Any, Dict, Optional

from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class VacationDaysTool(BaseTool):
    """Tool for retrieving the remaining vacation days for a specific employee."""

    def __init__(self) -> None:
        """Initializes the VacationDaysTool instance."""
        super().__init__(
            name="get_remaining_vacation_days",
            description="Returns the total number of remaining vacation days for a given employee ID.",
            enabled=True,
        )

    @property
    def schema(self) -> Dict[str, Any]:
        """Defines the JSON Schema for the tool requiring the employee ID."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "The unique identifier of the employee (e.g., EMP001).",
                        }
                    },
                    "required": ["employee_id"],
                },
            },
        }

    async def _execute_tool(
        self, employee_id: Optional[str] = None, **kwargs: Any
    ) -> str:
        """
        Executes the tool logic strictly requiring the employee ID from the LLM.

        Args:
            employee_id: The unique identifier provided by the LLM.
            **kwargs: Additional execution context.

        Returns:
            A string message containing the vacation balance or a specific error.
        """
        if not employee_id:
            logger.warning("VacationDaysTool: Execution attempted without employee_id.")
            return "Error: Employee ID is missing. The user must provide their ID."

        balance = 15

        logger.info(f"Retrieved {balance} days for employee_id: {employee_id}")
        return f"Employee {employee_id} has {balance} vacation days remaining."
