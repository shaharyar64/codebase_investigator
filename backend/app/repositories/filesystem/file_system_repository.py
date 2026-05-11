"""Filesystem access for cloned repositories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.constants.repository import (
    IGNORED_DIRECTORIES,
    IGNORED_FILE_SUFFIXES,
)
from app.utils.exceptions import RepositoryException


@dataclass(frozen=True)
class FileEntry:
    """A text file discovered in a repository."""

    path: str
    size: int
    line_count: int


@dataclass(frozen=True)
class FileSlice:
    """A line-based excerpt from a repository file."""

    file: str
    start_line: int
    end_line: int
    content: str


class FileSystemRepository:
    """Read-only filesystem operations scoped to one repository root."""

    def __init__(self, root_path: str | Path, max_file_bytes: int) -> None:
        self._root_path = Path(root_path).resolve()
        self._max_file_bytes = max_file_bytes

    @property
    def root_path(self) -> Path:
        """Return the repository root path."""
        return self._root_path

    def list_files(self) -> list[FileEntry]:
        """Return analyzable text files under the repository root."""
        entries: list[FileEntry] = []
        if not self._root_path.exists():
            raise RepositoryException(
                "Repository path does not exist.",
                status_code=404,
            )

        for path in self._root_path.rglob("*"):
            if not path.is_file() or self._should_ignore(path):
                continue
            if path.stat().st_size > self._max_file_bytes:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            relative = self._relative(path)
            entries.append(
                FileEntry(
                    path=relative,
                    size=path.stat().st_size,
                    line_count=len(text.splitlines()),
                )
            )
        return sorted(entries, key=lambda entry: entry.path)

    def file_exists(self, relative_path: str) -> bool:
        """Return whether a relative repository path exists."""
        return self._resolve_safe(relative_path).is_file()

    def line_count(self, relative_path: str) -> int:
        """Return line count for a text file."""
        text = self.read_text(relative_path)
        return len(text.splitlines())

    def read_text(self, relative_path: str) -> str:
        """Read a text file from the repository."""
        path = self._resolve_safe(relative_path)
        if not path.is_file():
            raise RepositoryException(
                f"File not found: {relative_path}",
                status_code=404,
            )
        if path.stat().st_size > self._max_file_bytes:
            raise RepositoryException(f"File is too large to inspect: {relative_path}")
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryException(
                f"File is not UTF-8 text: {relative_path}"
            ) from exc

    def read_slice(
        self,
        relative_path: str,
        start_line: int,
        end_line: int,
    ) -> FileSlice:
        """Read an inclusive line range from a text file."""
        if start_line < 1 or end_line < start_line:
            raise RepositoryException("Invalid line range.")
        lines = self.read_text(relative_path).splitlines()
        if start_line > len(lines):
            raise RepositoryException(
                f"Line range starts beyond end of file: {relative_path}"
            )
        bounded_end = min(end_line, len(lines))
        selected = lines[start_line - 1 : bounded_end]
        return FileSlice(
            file=relative_path,
            start_line=start_line,
            end_line=bounded_end,
            content="\n".join(selected),
        )

    def _should_ignore(self, path: Path) -> bool:
        parts = set(path.relative_to(self._root_path).parts)
        if parts.intersection(IGNORED_DIRECTORIES):
            return True
        return path.suffix.lower() in IGNORED_FILE_SUFFIXES

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self._root_path).as_posix()

    def _resolve_safe(self, relative_path: str) -> Path:
        candidate = (self._root_path / relative_path).resolve()
        try:
            candidate.relative_to(self._root_path)
        except ValueError as exc:
            raise RepositoryException("Path escapes repository root.") from exc
        return candidate
