"""Chat API routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Ask a plain-English question about a cloned repository."""
    return await service.ask(payload)

