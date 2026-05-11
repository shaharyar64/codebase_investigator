"""Chat orchestration service."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import Request

from app.agents.auditor.agent import AuditorAgent
from app.agents.investigator.agent import InvestigatorAgent
from app.models.repository import RepositoryStatus
from app.repositories.database.repository_store import RepositoryStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session.session_service import SessionService
from app.utils.exceptions import AppException, NotFoundException, RepositoryException
from app.utils.sse import encode_sse

logger = logging.getLogger(__name__)


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

    async def ask_stream(
        self,
        *,
        http_request: Request,
        request: ChatRequest,
    ) -> AsyncIterator[bytes]:
        """Stream investigation tokens over SSE, then emit final metadata."""
        try:
            async for frame in self._ask_stream_frames(http_request, request):
                yield frame
        except AppException as exc:
            yield encode_sse(
                "error",
                {"message": exc.message, "code": exc.code},
            )
        except Exception:
            logger.exception("Chat stream failed")
            yield encode_sse(
                "error",
                {
                    "message": "Investigation failed.",
                    "code": "internal_error",
                },
            )

    async def _ask_stream_frames(
        self,
        http_request: Request,
        request: ChatRequest,
    ) -> AsyncIterator[bytes]:
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

        yield encode_sse("session", {"session_id": conversation.id})

        if await http_request.is_disconnected():
            return

        yield encode_sse("status", {"phase": "searching"})
        evidence = await self._investigator_agent.collect_evidence(
            repository=repository,
            question=request.question,
            history=history,
        )

        if await http_request.is_disconnected():
            return

        yield encode_sse("status", {"phase": "answering"})

        parts: list[str] = []
        async for delta in self._investigator_agent.stream_answer_markdown(
            repository=repository,
            question=request.question,
            history=history,
            evidence=evidence,
        ):
            if await http_request.is_disconnected():
                return
            parts.append(delta)
            if delta:
                yield encode_sse("message", {"content": delta})

        answer_text = "".join(parts).strip()
        if not answer_text:
            yield encode_sse(
                "error",
                {
                    "message": "The model returned an empty answer.",
                    "code": "empty_answer",
                },
            )
            return

        if await http_request.is_disconnected():
            return

        citations, reasoning_summary = (
            await self._investigator_agent.extract_citations_and_summary(
                question=request.question,
                answer_markdown=answer_text,
                evidence=evidence,
            )
        )
        audit = await self._auditor_agent.audit(
            repository=repository,
            question=request.question,
            answer=answer_text,
            citations=citations,
            reasoning_summary=reasoning_summary,
        )
        assistant_message = await self._session_service.add_assistant_message(
            session_id=conversation.id,
            answer=answer_text,
            reasoning_summary=reasoning_summary,
            citations=citations,
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

        yield encode_sse(
            "done",
            {
                "status": "complete",
                "session_id": conversation.id,
                "citations": [c.model_dump() for c in citations],
                "audit": audit.model_dump(),
                "reasoning_summary": reasoning_summary,
            },
        )
