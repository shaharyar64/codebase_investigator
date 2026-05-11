"""Git clone service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from git import GitCommandError, Repo

from app.utils.exceptions import RepositoryException


@dataclass(frozen=True)
class CloneResult:
    """Metadata returned after cloning a repository."""

    local_path: str
    default_branch: str | None
    commit_sha: str | None


class GitRepositoryCloner:
    """Clone public repositories into local storage."""

    async def clone(self, *, url: str, target_path: Path) -> CloneResult:
        """Clone a repository asynchronously by offloading GitPython work."""
        return await asyncio.to_thread(self._clone_sync, url, target_path)

    def _clone_sync(self, url: str, target_path: Path) -> CloneResult:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and any(target_path.iterdir()):
            raise RepositoryException("Repository storage path already exists.")

        try:
            repository = Repo.clone_from(
                url,
                target_path,
                multi_options=["--depth=1"],
            )
        except GitCommandError as exc:
            raise RepositoryException(
                "Unable to clone repository. Confirm it is public and reachable."
            ) from exc

        try:
            default_branch = repository.active_branch.name
        except TypeError:
            default_branch = None

        commit_sha = repository.head.commit.hexsha if repository.head else None
        return CloneResult(
            local_path=str(target_path.resolve()),
            default_branch=default_branch,
            commit_sha=commit_sha,
        )

