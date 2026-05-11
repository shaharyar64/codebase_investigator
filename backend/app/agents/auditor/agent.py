"""Independent audit agent."""

from __future__ import annotations

from typing import Any

from app.agents.prompts.auditor import AUDITOR_PROMPT
from app.core.config.settings import Settings
from app.models.repository import Repository
from app.repositories.filesystem.file_system_repository import FileSystemRepository
from app.schemas.chat import AuditResult, Citation
from app.services.ai.openai_service import OpenAIService


class AuditorAgent:
    """Verify generated answers and citations independently."""

    def __init__(self, *, ai_service: OpenAIService, settings: Settings) -> None:
        self._ai_service = ai_service
        self._settings = settings

    async def audit(
        self,
        *,
        repository: Repository,
        question: str,
        answer: str,
        citations: list[Citation],
        reasoning_summary: str,
    ) -> AuditResult:
        """Run mechanical and AI audit checks."""
        file_system = FileSystemRepository(
            repository.local_path,
            max_file_bytes=self._settings.max_file_bytes,
        )
        mechanical_warnings, checked_citations = self._check_citations(
            file_system=file_system,
            citations=citations,
        )

        audit_payload = await self._ai_service.generate_json(
            instructions=AUDITOR_PROMPT,
            payload={
                "question": question,
                "answer": answer,
                "reasoning_summary": reasoning_summary,
                "repository": {
                    "id": repository.id,
                    "name": repository.name,
                    "url": repository.url,
                    "metadata": repository.metadata_json,
                },
                "checked_citations": [
                    citation.model_dump() for citation in checked_citations
                ],
                "mechanical_warnings": mechanical_warnings,
            },
            schema_name="answer_audit",
            schema=self._audit_schema(),
            model=self._settings.openai_audit_model,
        )

        warnings = mechanical_warnings + list(audit_payload.get("warnings", []))
        unsupported_claims = list(audit_payload.get("unsupported_claims", []))
        verified = (
            bool(audit_payload.get("verified", False))
            and not warnings
            and not unsupported_claims
        )
        return AuditResult(
            verified=verified,
            warnings=warnings,
            unsupported_claims=unsupported_claims,
            checked_citations=checked_citations,
            details=str(audit_payload.get("details", "")).strip(),
        )

    def _check_citations(
        self,
        *,
        file_system: FileSystemRepository,
        citations: list[Citation],
    ) -> tuple[list[str], list[Citation]]:
        warnings: list[str] = []
        checked: list[Citation] = []

        if not citations:
            warnings.append("The answer did not include citations.")
            return warnings, checked

        for citation in citations:
            if not file_system.file_exists(citation.file):
                warnings.append(f"Citation file does not exist: {citation.file}")
                continue
            if citation.end_line < citation.start_line:
                warnings.append(f"Citation has invalid line range: {citation.file}")
                continue
            try:
                line_count = file_system.line_count(citation.file)
            except Exception:
                warnings.append(f"Citation file cannot be read: {citation.file}")
                continue
            if citation.start_line > line_count:
                warnings.append(
                    f"Citation starts beyond end of file: {citation.file}"
                )
                continue
            try:
                file_slice = file_system.read_slice(
                    citation.file,
                    citation.start_line,
                    citation.end_line,
                )
            except Exception:
                warnings.append(f"Citation range cannot be read: {citation.file}")
                continue
            checked.append(
                Citation(
                    file=citation.file,
                    start_line=file_slice.start_line,
                    end_line=file_slice.end_line,
                    excerpt=file_slice.content[:3000],
                )
            )

        return warnings, checked

    def _audit_schema(self) -> dict[str, Any]:
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
                "verified": {"type": "boolean"},
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "unsupported_claims": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "checked_citations": {
                    "type": "array",
                    "items": citation_schema,
                },
                "details": {"type": "string"},
            },
            "required": [
                "verified",
                "warnings",
                "unsupported_claims",
                "checked_citations",
                "details",
            ],
        }

