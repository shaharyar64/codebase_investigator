"""Session API routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_session_service
from app.schemas.session import SessionResponse
from app.services.session.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Return conversation history."""
    return await service.get_session_response(session_id)

