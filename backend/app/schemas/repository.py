"""Repository request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RepositoryCreate(BaseModel):
    """Request body for creating a repository investigation target."""

    url: HttpUrl = Field(..., description="Public GitHub repository URL")


class RepositoryResponse(BaseModel):
    """Repository details returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    owner: str
    name: str
    status: str
    local_path: str
    default_branch: str | None = None
    commit_sha: str | None = None
    file_count: int
    line_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

