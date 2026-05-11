"""Conversation session service."""

from __future__ import annotations

from app.models.chat_message import ChatMessage
from app.models.session import ConversationSession
from app.repositories.database.session_store import SessionStore
from app.schemas.chat import AuditResult, ChatMessageResponse, Citation
from app.schemas.session import SessionResponse
from app.utils.exceptions import NotFoundException, RepositoryException


class SessionService:
    """Manage multi-turn conversation sessions and chat history."""

    def __init__(self, *, store: SessionStore) -> None:
        self._store = store

    async def get_or_create_session(
        self,
        *,
        repository_id: str,
        session_id: str | None,
        first_question: str,
    ) -> ConversationSession:
        """Return an existing session or create a new one."""
        if session_id:
            conversation = await self._store.get_session(session_id)
            if conversation is None:
                raise NotFoundException("Session not found.")
            if conversation.repository_id != repository_id:
                raise RepositoryException("Session does not belong to repository.")
            return conversation

        title = first_question.strip().replace("\n", " ")[:80] or "Investigation"
        return await self._store.create_session(
            repository_id=repository_id,
            title=title,
        )

    async def add_user_message(
        self,
        *,
        session_id: str,
        content: str,
    ) -> ChatMessage:
        """Persist a user message."""
        return await self._store.add_message(
            session_id=session_id,
            role="user",
            content=content,
        )

    async def list_messages(self, session_id: str) -> list[ChatMessage]:
        """Return session history using an explicit async database query."""
        return await self._store.list_messages(session_id)

    async def add_assistant_message(
        self,
        *,
        session_id: str,
        answer: str,
        reasoning_summary: str,
        citations: list[Citation],
        audit: AuditResult,
    ) -> ChatMessage:
        """Persist an assistant answer."""
        return await self._store.add_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            reasoning_summary=reasoning_summary,
            citations=[citation.model_dump() for citation in citations],
            audit=audit.model_dump(),
        )

    async def persist_audit(
        self,
        *,
        session_id: str,
        message_id: str,
        audit: AuditResult,
    ) -> None:
        """Persist a separate audit log row."""
        await self._store.add_audit_log(
            session_id=session_id,
            message_id=message_id,
            verified=audit.verified,
            warnings=audit.warnings,
            unsupported_claims=audit.unsupported_claims,
            checked_citations=[
                citation.model_dump() for citation in audit.checked_citations
            ],
            details=audit.details,
        )

    async def refresh_memory(
        self,
        *,
        conversation: ConversationSession,
        messages: list[ChatMessage],
    ) -> None:
        """Update compact, deterministic session memory from recent turns."""
        recent_messages = messages[-12:]
        summary_lines = [
            f"{message.role}: {message.content[:500].replace(chr(10), ' ')}"
            for message in recent_messages
        ]
        await self._store.update_memory(
            conversation,
            memory_summary="\n".join(summary_lines),
        )

    async def get_session_response(self, session_id: str) -> SessionResponse:
        """Return a session and its message history."""
        conversation = await self._store.get_session(session_id)
        if conversation is None:
            raise NotFoundException("Session not found.")
        return self.to_response(conversation)

    def to_response(self, conversation: ConversationSession) -> SessionResponse:
        """Convert a conversation ORM entity to an API response."""
        return SessionResponse(
            id=conversation.id,
            repository_id=conversation.repository_id,
            title=conversation.title,
            memory_summary=conversation.memory_summary,
            messages=[
                self._message_to_response(message)
                for message in list(conversation.messages)
            ],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    def _message_to_response(self, message: ChatMessage) -> ChatMessageResponse:
        citations: list[Citation] = []
        for item in message.citations_json or []:
            try:
                citations.append(Citation(**item))
            except Exception:
                continue
        return ChatMessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            reasoning_summary=message.reasoning_summary,
            citations=citations,
            audit=message.audit_json,
            created_at=message.created_at,
        )
