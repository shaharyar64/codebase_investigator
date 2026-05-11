"""Conversation session ORM model."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ConversationSession(Base, TimestampMixin):
    """A multi-turn conversation scoped to one repository."""

    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="Investigation")
    memory_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    repository = relationship("Repository", back_populates="sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

