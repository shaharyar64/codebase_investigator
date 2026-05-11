"""Chat and audit schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """A file and line range that supports an answer claim."""

    file: str
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)
    excerpt: str | None = None


class AuditResult(BaseModel):
    """Independent verification result for an answer."""

    verified: bool
    warnings: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    checked_citations: list[Citation] = Field(default_factory=list)
    details: str = ""


class ChatRequest(BaseModel):
    """Request body for asking a repository question."""

    repository_id: str
    question: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Grounded answer returned by the investigation pipeline."""

    session_id: str
    answer: str
    citations: list[Citation]
    audit: AuditResult
    reasoning_summary: str


class ChatMessageResponse(BaseModel):
    """Stored chat message response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    reasoning_summary: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    audit: dict[str, Any] | None = None
    created_at: datetime

