"""High-level repository application service."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from app.core.config.settings import Settings
from app.models.repository import Repository, RepositoryStatus
from app.repositories.database.repository_store import RepositoryStore
from app.repositories.filesystem.file_system_repository import FileSystemRepository
from app.schemas.repository import RepositoryResponse
from app.services.analysis.repository_analyzer import RepositoryAnalyzer
from app.services.repository.cloner import GitRepositoryCloner
from app.services.repository.github_url import GitHubUrlParser
from app.utils.exceptions import NotFoundException, RepositoryException

logger = logging.getLogger(__name__)


class RepositoryService:
    """Coordinate repository validation, cloning, indexing, and retrieval."""

    def __init__(
        self,
        *,
        store: RepositoryStore,
        url_parser: GitHubUrlParser,
        cloner: GitRepositoryCloner,
        analyzer: RepositoryAnalyzer,
        settings: Settings,
    ) -> None:
        self._store = store
        self._url_parser = url_parser
        self._cloner = cloner
        self._analyzer = analyzer
        self._settings = settings

    async def submit_repository(self, raw_url: str) -> RepositoryResponse:
        """Validate, clone, analyze, and persist a public GitHub repository."""
        parsed = self._url_parser.parse(raw_url)
        existing = await self._store.find_by_url(parsed.url)
        if existing and existing.status != RepositoryStatus.FAILED.value:
            return self.to_response(existing)

        repository_id = str(uuid4())
        target_path = self._target_path(repository_id, parsed.owner, parsed.name)
        repository = await self._store.create(
            repository_id=repository_id,
            url=parsed.url,
            owner=parsed.owner,
            name=parsed.name,
            local_path=str(target_path),
            status=RepositoryStatus.CLONING.value,
        )

        try:
            clone_result = await self._cloner.clone(
                url=parsed.url,
                target_path=target_path,
            )
            await self._store.update_status(
                repository,
                status=RepositoryStatus.INDEXING.value,
            )
            file_system = FileSystemRepository(
                clone_result.local_path,
                max_file_bytes=self._settings.max_file_bytes,
            )
            metadata = self._analyzer.analyze(file_system)
            metadata["clone"] = {
                "default_branch": clone_result.default_branch,
                "commit_sha": clone_result.commit_sha,
            }
            repository = await self._store.update_analysis(
                repository,
                status=RepositoryStatus.READY.value,
                default_branch=clone_result.default_branch,
                commit_sha=clone_result.commit_sha,
                file_count=int(metadata["file_count"]),
                line_count=int(metadata["line_count"]),
                metadata=metadata,
            )
            logger.info(
                "Repository indexed",
                extra={
                    "extra": {
                        "repository_id": repository.id,
                        "file_count": repository.file_count,
                    }
                },
            )
            return self.to_response(repository)
        except RepositoryException as exc:
            await self._store.update_status(
                repository,
                status=RepositoryStatus.FAILED.value,
                error_message=exc.message,
            )
            raise
        except Exception as exc:
            logger.exception("Repository ingestion failed")
            await self._store.update_status(
                repository,
                status=RepositoryStatus.FAILED.value,
                error_message=str(exc),
            )
            raise RepositoryException("Repository ingestion failed.") from exc

    async def get_repository(self, repository_id: str) -> Repository:
        """Return a repository entity or raise 404."""
        repository = await self._store.get(repository_id)
        if repository is None:
            raise NotFoundException("Repository not found.")
        return repository

    async def get_repository_response(self, repository_id: str) -> RepositoryResponse:
        """Return repository details as an API schema."""
        repository = await self.get_repository(repository_id)
        return self.to_response(repository)

    async def list_repositories(self, limit: int = 20) -> list[RepositoryResponse]:
        """Return recent repositories."""
        repositories = await self._store.list_recent(limit=limit)
        return [self.to_response(repository) for repository in repositories]

    def to_response(self, repository: Repository) -> RepositoryResponse:
        """Convert a repository ORM entity to an API response."""
        return RepositoryResponse(
            id=repository.id,
            url=repository.url,
            owner=repository.owner,
            name=repository.name,
            status=repository.status,
            local_path=repository.local_path,
            default_branch=repository.default_branch,
            commit_sha=repository.commit_sha,
            file_count=repository.file_count,
            line_count=repository.line_count,
            metadata=repository.metadata_json or {},
            error_message=repository.error_message,
            created_at=repository.created_at,
            updated_at=repository.updated_at,
        )

    def _target_path(self, repository_id: str, owner: str, name: str) -> Path:
        root = self._settings.repository_root
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{owner}__{name}__{repository_id}"

