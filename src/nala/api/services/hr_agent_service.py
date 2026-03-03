import uuid
from datetime import datetime, timezone
from typing import Optional

from nala.api.schemas.chat import ChatRequest, ChatResponse
from nala.athomic.ai.agents.factory import AgentFactory
from nala.athomic.ai.llm.manager import LLMManager, llm_manager
from nala.athomic.ai.prompts.factory import PromptServiceFactory
from nala.athomic.ai.schemas import ChatMessage, MessageRole
from nala.athomic.config import get_settings
from nala.athomic.services.base import BaseService


class HRAssistantService(BaseService):
    """
    Orchestrator for HR Assistant operations.

    Uses a single AgentService instance as a singleton to handle requests
    dynamically, passing context variables at runtime.
    """

    def __init__(
        self,
        llm_manager_instance: Optional[LLMManager] = llm_manager,
        profile_name: str = "hr_assistant",
    ) -> None:
        super().__init__(service_name="hr_assistant_service")
        self.profile_name = profile_name
        self._llm_manager = llm_manager_instance
        self.prompt_service = PromptServiceFactory.create()
        self.settings = get_settings()

        # Singleton: Instantiated once, thread-safety is managed in .run()
        self.agent = AgentFactory.create(
            profile_name=self.profile_name,
            llm_manager_instance=self._llm_manager,
        )

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a chat request by passing session data as runtime context.
        """
        session_id = request.session_id or str(uuid.uuid4())
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Dynamic runtime context
        runtime_context = {
            "employee_id": request.employee_id,
            "current_date": current_date,
            "language": "en",
        }

        system_content = self.prompt_service.render(
            name="hr/assistant",
            variables=runtime_context,
        )

        # Execution using local scope variables for thread safety
        reply = await self.agent.run(
            input_message=request.message,
            thread_id=session_id,
            history=[ChatMessage(role=MessageRole.SYSTEM, content=system_content)],
            **runtime_context,
        )

        return ChatResponse(reply=reply, session_id=session_id)
