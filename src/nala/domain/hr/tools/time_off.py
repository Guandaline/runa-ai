from datetime import datetime
from typing import Any, Dict, Optional

from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class TimeOffTool(BaseTool):
    """Tool for requesting time off with strict parameter validation."""

    def __init__(self) -> None:
        """Initializes the TimeOffTool instance."""
        super().__init__(
            name="request_time_off",
            description="Requests time off for an employee. Requires employee_id, start_date, and end_date.",
            enabled=True,
        )

    @property
    def schema(self) -> Dict[str, Any]:
        """Defines the strict JSON Schema requiring all necessary parameters."""
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
                            "description": "The unique identifier of the employee.",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date in YYYY-MM-DD format.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date in YYYY-MM-DD format.",
                        },
                    },
                    "required": ["employee_id", "start_date", "end_date"],
                },
            },
        }

    async def _execute_tool(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Executes the time off request logic validating dates and balances.

        Args:
            employee_id: The ID provided by the LLM.
            start_date: Start date of the leave.
            end_date: End date of the leave.
            **kwargs: Additional execution context.

        Returns:
            A status message indicating success or specific validation errors.
        """
        if not employee_id or not start_date or not end_date:
            logger.warning("TimeOffTool: Execution attempted with missing parameters.")
            return "Error: Missing parameters. Please ask the user to provide their employee_id, start date, and end date."

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return (
                "Error: Invalid date format. Please use YYYY-MM-DD (e.g., 2026-12-31)."
            )

        if start_dt <= datetime.now():
            return "Error: The start date must be a future date."

        if end_dt < start_dt:
            return "Error: The end date cannot be earlier than the start date."

        requested_days = (end_dt - start_dt).days + 1
        simulated_balance = 15

        if requested_days > simulated_balance:
            return (
                f"Error: Insufficient balance. You requested {requested_days} days, "
                f"but only have {simulated_balance} available."
            )

        logger.info(f"Time off requested for {employee_id}: {start_date} to {end_date}")

        return (
            f"Success: Time off requested from {start_date} to {end_date} ({requested_days} days) "
            f"for employee {employee_id}. Remaining balance: {simulated_balance - requested_days} days."
        )
