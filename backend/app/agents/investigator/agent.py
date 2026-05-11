"""Repository investigation agent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.agents.prompts.investigator import (
    INVESTIGATOR_PROMPT,
    SEARCH_PLANNER_PROMPT,
)
from app.core.config.settings import Settings
from app.models.chat_message import ChatMessage
from app.models.repository import Repository
from app.repositories.filesystem.file_system_repository import FileSystemRepository
from app.schemas.chat import Citation
from app.services.ai.openai_service import OpenAIService
from app.services.search.ripgrep_service import CodeContext, RipgrepSearchService


@dataclass(frozen=True)
class InvestigationResult:
    """Structured output from the investigation agent."""

    answer: str
    citations: list[Citation]
    reasoning_summary: str
    search_terms: list[str]
    inspected_files: list[str]


class InvestigatorAgent:
    """Plan searches, inspect files, and generate grounded answers."""

    def __init__(
        self,
        *,
        ai_service: OpenAIService,
        search_service: RipgrepSearchService,
        settings: Settings,
    ) -> None:
        self._ai_service = ai_service
        self._search_service = search_service
        self._settings = settings

    async def answer_question(
        self,
        *,
        repository: Repository,
        question: str,
        history: list[ChatMessage],
    ) -> InvestigationResult:
        """Investigate a repository question and return a grounded answer."""
        file_system = FileSystemRepository(
            repository.local_path,
            max_file_bytes=self._settings.max_file_bytes,
        )
        plan = await self._plan_searches(
            repository=repository,
            question=question,
            history=history,
        )
        search_terms = plan.get("search_terms", []) or self._fallback_terms(question)
        candidate_files = plan.get("candidate_files", [])

        hits = await self._search_service.search_many(
            file_system=file_system,
            queries=search_terms,
            max_results=self._settings.max_search_results,
        )
        contexts = self._search_service.build_contexts(
            file_system=file_system,
            hits=hits,
            window=self._settings.search_context_window,
            max_contexts=self._settings.max_context_files,
        )
        contexts.extend(
            self._search_service.read_candidate_files(
                file_system=file_system,
                file_paths=candidate_files,
                max_contexts=max(0, self._settings.max_context_files - len(contexts)),
            )
        )

        answer_payload = await self._generate_answer(
            repository=repository,
            question=question,
            history=history,
            contexts=contexts,
            search_terms=search_terms,
        )
        citations = self._parse_citations(answer_payload.get("citations", []))
        inspected_files = sorted({context.file for context in contexts})
        return InvestigationResult(
            answer=str(answer_payload.get("answer", "")).strip(),
            citations=citations,
            reasoning_summary=str(answer_payload.get("reasoning_summary", "")).strip(),
            search_terms=search_terms,
            inspected_files=inspected_files,
        )

    async def _plan_searches(
        self,
        *,
        repository: Repository,
        question: str,
        history: list[ChatMessage],
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "repository": self._repository_summary(repository),
            "recent_history": self._history_for_prompt(history),
        }
        try:
            return await self._ai_service.generate_json(
                instructions=SEARCH_PLANNER_PROMPT,
                payload=payload,
                schema_name="search_plan",
                schema=self._search_plan_schema(),
            )
        except Exception:
            return {
                "search_terms": self._fallback_terms(question),
                "candidate_files": [],
                "investigation_focus": "Fallback lexical search.",
            }

    async def _generate_answer(
        self,
        *,
        repository: Repository,
        question: str,
        history: list[ChatMessage],
        contexts: list[CodeContext],
        search_terms: list[str],
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "repository": self._repository_summary(repository),
            "recent_history": self._history_for_prompt(history),
            "search_terms": search_terms,
            "code_contexts": [context.__dict__ for context in contexts],
        }
        return await self._ai_service.generate_json(
            instructions=INVESTIGATOR_PROMPT,
            payload=payload,
            schema_name="investigation_answer",
            schema=self._answer_schema(),
        )

    def _repository_summary(self, repository: Repository) -> dict[str, Any]:
        metadata = repository.metadata_json or {}
        return {
            "id": repository.id,
            "url": repository.url,
            "owner": repository.owner,
            "name": repository.name,
            "default_branch": repository.default_branch,
            "commit_sha": repository.commit_sha,
            "file_count": repository.file_count,
            "line_count": repository.line_count,
            "languages": metadata.get("languages", {}),
            "important_files": metadata.get("important_files", [])[:40],
            "tree": metadata.get("tree", [])[:500],
            "manifests": metadata.get("manifests", [])[:12],
        }

    def _history_for_prompt(self, history: list[ChatMessage]) -> list[dict[str, str]]:
        messages = history[-10:]
        return [
            {
                "role": message.role,
                "content": message.content[:2500],
                "reasoning_summary": (message.reasoning_summary or "")[:1000],
            }
            for message in messages
        ]

    def _parse_citations(self, raw_citations: Any) -> list[Citation]:
        citations: list[Citation] = []
        if not isinstance(raw_citations, list):
            return citations
        for item in raw_citations:
            try:
                citations.append(Citation(**item))
            except Exception:
                continue
        return citations

    def _fallback_terms(self, question: str) -> list[str]:
        lower = question.lower()
        terms = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", question)
        mapped_terms: list[str] = []
        if any(term in lower for term in ["auth", "login", "signup", "jwt", "token"]):
            mapped_terms.extend(
                [
                    "auth",
                    "authenticate",
                    "authorization",
                    "jwt",
                    "token",
                    "login",
                    "signup",
                    "middleware",
                ]
            )
        if "async" in lower:
            mapped_terms.extend(["async", "await", "create_task", "gather"])
        if "error" in lower:
            mapped_terms.extend(["exception", "error", "raise", "handler"])
        mapped_terms.extend(terms[:10])

        seen: set[str] = set()
        cleaned: list[str] = []
        for term in mapped_terms:
            normalized = term.strip()
            if normalized.lower() in seen:
                continue
            seen.add(normalized.lower())
            cleaned.append(normalized)
        return cleaned[:14] or [question[:80]]

    def _search_plan_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 14,
                },
                "candidate_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 10,
                },
                "investigation_focus": {"type": "string"},
            },
            "required": [
                "search_terms",
                "candidate_files",
                "investigation_focus",
            ],
        }

    def _answer_schema(self) -> dict[str, Any]:
        citation_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file": {"type": "string"},
                "start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": 1},
                "excerpt": {"type": ["string", "null"]},
            },
            "required": ["file", "start_line", "end_line", "excerpt"],
        }
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "answer": {"type": "string"},
                "citations": {"type": "array", "items": citation_schema},
                "reasoning_summary": {"type": "string"},
            },
            "required": ["answer", "citations", "reasoning_summary"],
        }

