"""Audit log ORM model."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Persistent audit record for an assistant answer."""

    __tablename__ = "audit_logs"

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
    message_id: Mapped[str] = mapped_column(
        ForeignKey("chat_messages.id"),
        nullable=False,
        index=True,
    )
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    warnings_json: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    unsupported_claims_json: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    checked_citations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

