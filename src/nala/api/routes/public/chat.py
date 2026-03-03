from fastapi import APIRouter, Depends

from nala.api.schemas.chat import ChatRequest, ChatResponse
from nala.api.services.hr_agent_service import HRAssistantService

router = APIRouter(prefix="/chat", tags=["HR Assistant"])


def get_hr_assistant_service() -> HRAssistantService:
    """Provides an instance of the HR Assistant Service for dependency injection.

    Returns:
        An initialized HRAssistantService ready to process chat requests.
    """
    return HRAssistantService()


@router.post("", response_model=ChatResponse)
async def process_chat_message(
    request: ChatRequest,
    service: HRAssistantService = Depends(get_hr_assistant_service),
) -> ChatResponse:
    """Endpoint for processing natural language requests to the HR Assistant.

    Args:
        request: The incoming chat payload containing the employee ID and message.
        service: The injected HRAssistantService instance.

    Returns:
        The agent's response and the active session identifier.
    """
    return await service.process_chat(request)
