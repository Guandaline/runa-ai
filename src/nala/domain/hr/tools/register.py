from nala.athomic.ai.tools.registry import tool_registry

from .policy import CompanyPolicyTool
from .time_off import TimeOffTool
from .vacation import VacationDaysTool


class HRToolRegister:
    """Registrar class responsible for initializing and registering HR domain tools.

    This class encapsulates the setup logic required to make the HR-specific
    tools available to the global AI tool registry, allowing agents to resolve
    and execute them dynamically during runtime.
    """

    @classmethod
    def register_all(cls) -> None:
        """Instantiates and registers all HR tools into the global registry."""
        tools = [
            VacationDaysTool(),
            TimeOffTool(),
            CompanyPolicyTool(),
        ]

        for tool in tools:
            tool_registry.register(name=tool.name, item_instance=tool)
