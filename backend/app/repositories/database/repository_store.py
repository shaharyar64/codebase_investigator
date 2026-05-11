"""Database access for repositories."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository


class RepositoryStore:
    """Repository pattern wrapper for repository persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        repository_id: str,
        url: str,
        owner: str,
        name: str,
        local_path: str,
        status: str,
    ) -> Repository:
        """Create and persist a repository row."""
        repository = Repository(
            id=repository_id,
            url=url,
            owner=owner,
            name=name,
            local_path=local_path,
            status=status,
        )
        self._session.add(repository)
        await self._session.commit()
        await self._session.refresh(repository)
        return repository

    async def get(self, repository_id: str) -> Repository | None:
        """Return a repository by ID."""
        return await self._session.get(Repository, repository_id)

    async def find_by_url(self, url: str) -> Repository | None:
        """Return the newest repository row for a normalized URL."""
        statement = (
            select(Repository)
            .where(Repository.url == url)
            .order_by(Repository.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> list[Repository]:
        """Return recently created repositories."""
        statement = (
            select(Repository)
            .order_by(Repository.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def update_status(
        self,
        repository: Repository,
        *,
        status: str,
        error_message: str | None = None,
    ) -> Repository:
        """Update repository status."""
        repository.status = status
        repository.error_message = error_message
        await self._session.commit()
        await self._session.refresh(repository)
        return repository

    async def update_analysis(
        self,
        repository: Repository,
        *,
        status: str,
        default_branch: str | None,
        commit_sha: str | None,
        file_count: int,
        line_count: int,
        metadata: dict[str, Any],
    ) -> Repository:
        """Persist clone and analysis metadata."""
        repository.status = status
        repository.default_branch = default_branch
        repository.commit_sha = commit_sha
        repository.file_count = file_count
        repository.line_count = line_count
        repository.metadata_json = metadata
        repository.error_message = None
        await self._session.commit()
        await self._session.refresh(repository)
        return repository
