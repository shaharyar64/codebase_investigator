"""Conversation session schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import ChatMessageResponse


class SessionResponse(BaseModel):
    """Conversation history for one repository investigation session."""

    id: str
    repository_id: str
    title: str
    memory_summary: str = ""
    messages: list[ChatMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

