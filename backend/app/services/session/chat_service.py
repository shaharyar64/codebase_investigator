"""Chat orchestration service."""

from __future__ import annotations

from app.agents.auditor.agent import AuditorAgent
from app.agents.investigator.agent import InvestigatorAgent
from app.models.repository import RepositoryStatus
from app.repositories.database.repository_store import RepositoryStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session.session_service import SessionService
from app.utils.exceptions import NotFoundException, RepositoryException


class ChatService:
    """Coordinate multi-turn investigation, answer generation, and audit."""

    def __init__(
        self,
        *,
        repository_store: RepositoryStore,
        session_service: SessionService,
        investigator_agent: InvestigatorAgent,
        auditor_agent: AuditorAgent,
    ) -> None:
        self._repository_store = repository_store
        self._session_service = session_service
        self._investigator_agent = investigator_agent
        self._auditor_agent = auditor_agent

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """Answer a repository question and persist the full interaction."""
        repository = await self._repository_store.get(request.repository_id)
        if repository is None:
            raise NotFoundException("Repository not found.")
        if repository.status != RepositoryStatus.READY.value:
            raise RepositoryException(
                f"Repository is not ready for chat. Current status: {repository.status}"
            )

        conversation = await self._session_service.get_or_create_session(
            repository_id=repository.id,
            session_id=request.session_id,
            first_question=request.question,
        )
        history = await self._session_service.list_messages(conversation.id)
        user_message = await self._session_service.add_user_message(
            session_id=conversation.id,
            content=request.question,
        )
        history.append(user_message)

        investigation = await self._investigator_agent.answer_question(
            repository=repository,
            question=request.question,
            history=history,
        )
        audit = await self._auditor_agent.audit(
            repository=repository,
            question=request.question,
            answer=investigation.answer,
            citations=investigation.citations,
            reasoning_summary=investigation.reasoning_summary,
        )
        assistant_message = await self._session_service.add_assistant_message(
            session_id=conversation.id,
            answer=investigation.answer,
            reasoning_summary=investigation.reasoning_summary,
            citations=investigation.citations,
            audit=audit,
        )
        await self._session_service.persist_audit(
            session_id=conversation.id,
            message_id=assistant_message.id,
            audit=audit,
        )
        await self._session_service.refresh_memory(
            conversation=conversation,
            messages=history + [assistant_message],
        )

        return ChatResponse(
            session_id=conversation.id,
            answer=investigation.answer,
            citations=investigation.citations,
            audit=audit,
            reasoning_summary=investigation.reasoning_summary,
        )
