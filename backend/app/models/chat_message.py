"""Chat message ORM model."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ChatMessage(Base, TimestampMixin):
    """A user or assistant message in an investigation session."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_sessions.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    audit_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    session = relationship("ConversationSession", back_populates="messages")

