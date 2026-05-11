"""Repository ORM model."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class RepositoryStatus(str, Enum):
    """Lifecycle states for cloned repositories."""

    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Repository(Base, TimestampMixin):
    """A public GitHub repository cloned for investigation."""

    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    local_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=RepositoryStatus.CLONING.value,
        nullable=False,
    )
    file_count: Mapped[int] = mapped_column(default=0, nullable=False)
    line_count: Mapped[int] = mapped_column(default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sessions = relationship(
        "ConversationSession",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
