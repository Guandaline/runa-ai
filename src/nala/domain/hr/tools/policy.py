#
# src/nala/domain/hr/tools/policy.py
#
from typing import Any, Dict, Optional

from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class CompanyPolicyTool(BaseTool):
    """Tool for retrieving official company policies based on a specific topic."""

    def __init__(self) -> None:
        """Initializes the CompanyPolicyTool instance."""
        super().__init__(
            name="get_company_policy",
            description="Retrieves the official company policy text for a given topic.",
            enabled=True,
        )

    @property
    def schema(self) -> Dict[str, Any]:
        """Defines the JSON Schema for the tool required by the LLM."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The subject of the policy (e.g., 'vacation', 'remote work').",
                        }
                    },
                    "required": ["topic"],
                },
            },
        }

    async def _execute_tool(self, topic: Optional[str] = None, **kwargs: Any) -> str:
        """
        Executes the policy lookup with normalized topic matching.

        Args:
            topic: The subject of the inquiry.
            **kwargs: Additional context.
        """
        if not topic:
            return "Error: Topic not specified. Please tell me which policy you want to know about."

        normalized_topic = topic.lower()

        # Policy Knowledge Base (Simulated)
        if any(
            keyword in normalized_topic for keyword in ["vacation", "time off", "leave"]
        ):
            return (
                "Vacation Policy: Employees are entitled to 15 days of paid vacation per year. "
                "Requests must be submitted at least 2 weeks in advance via the HR portal."
            )

        if any(keyword in normalized_topic for keyword in ["remote", "home", "hybrid"]):
            return (
                "Remote Work Policy: Employees may work remotely up to 3 days a week "
                "subject to manager approval and team alignment."
            )

        if "sick" in normalized_topic:
            return (
                "Sick Leave Policy: Employees have 5 paid sick days per year. "
                "A medical certificate is mandatory for absences exceeding 2 consecutive days."
            )

        logger.debug(f"Policy lookup failed for topic: {topic}")
        return (
            f"I could not find a specific policy for '{topic}'. "
            "Try asking about 'vacation', 'remote work', or 'sick leave'."
        )
