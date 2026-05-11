"""Database access for sessions, messages, and audits."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.chat_message import ChatMessage
from app.models.session import ConversationSession


class SessionStore:
    """Repository pattern wrapper for conversation persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        *,
        repository_id: str,
        title: str,
    ) -> ConversationSession:
        """Create a new conversation session."""
        conversation = ConversationSession(
            repository_id=repository_id,
            title=title,
        )
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def get_session(self, session_id: str) -> ConversationSession | None:
        """Return a conversation session with messages."""
        statement = (
            select(ConversationSession)
            .options(selectinload(ConversationSession.messages))
            .where(ConversationSession.id == session_id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_messages(self, session_id: str) -> list[ChatMessage]:
        """Return messages for a session without lazy-loading relationships."""
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def add_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        reasoning_summary: str | None = None,
        citations: list[dict[str, Any]] | None = None,
        audit: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Persist a chat message."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            reasoning_summary=reasoning_summary,
            citations_json=citations or [],
            audit_json=audit,
        )
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def update_memory(
        self,
        conversation: ConversationSession,
        *,
        memory_summary: str,
    ) -> ConversationSession:
        """Update compact session memory."""
        conversation.memory_summary = memory_summary
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def add_audit_log(
        self,
        *,
        session_id: str,
        message_id: str,
        verified: bool,
        warnings: list[str],
        unsupported_claims: list[str],
        checked_citations: list[dict[str, Any]],
        details: str,
    ) -> AuditLog:
        """Persist an audit record."""
        audit_log = AuditLog(
            session_id=session_id,
            message_id=message_id,
            verified=verified,
            warnings_json=warnings,
            unsupported_claims_json=unsupported_claims,
            checked_citations_json=checked_citations,
            details=details,
        )
        self._session.add(audit_log)
        await self._session.commit()
        await self._session.refresh(audit_log)
        return audit_log
