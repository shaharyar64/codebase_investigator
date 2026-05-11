"""Chat API routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies.services import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session.chat_service import ChatService

router = APIRouter(tags=["chat"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/chat", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Ask a plain-English question about a cloned repository."""
    return await service.ask(payload)


@router.post("/chat/stream")
async def ask_question_stream(
    http_request: Request,
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Stream investigation answer tokens (SSE) then final citations and audit."""
    return StreamingResponse(
        service.ask_stream(http_request=http_request, request=payload),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )

