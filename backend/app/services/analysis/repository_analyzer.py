"""Repository structure analyzer."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from app.core.constants.repository import CODE_EXTENSIONS, IMPORTANT_FILENAMES
from app.repositories.filesystem.file_system_repository import FileSystemRepository


class RepositoryAnalyzer:
    """Build lightweight repository metadata from real files."""

    def analyze(self, file_system: FileSystemRepository) -> dict[str, Any]:
        """Return file counts, language stats, tree preview, and manifests."""
        files = file_system.list_files()
        language_counter: Counter[str] = Counter()
        important_files: list[str] = []

        for entry in files:
            path = Path(entry.path)
            language = CODE_EXTENSIONS.get(path.suffix.lower(), "Other")
            language_counter[language] += 1
            if path.name in IMPORTANT_FILENAMES or entry.path.startswith(
                ".github/workflows/"
            ):
                important_files.append(entry.path)

        manifests = self._read_important_files(file_system, important_files[:20])

        return {
            "file_count": len(files),
            "line_count": sum(entry.line_count for entry in files),
            "languages": dict(language_counter.most_common()),
            "tree": [entry.path for entry in files[:500]],
            "important_files": important_files,
            "manifests": manifests,
        }

    def _read_important_files(
        self,
        file_system: FileSystemRepository,
        important_files: list[str],
    ) -> list[dict[str, str]]:
        manifests: list[dict[str, str]] = []
        for file_path in important_files:
            try:
                content = file_system.read_slice(file_path, 1, 120).content
            except Exception:
                continue
            manifests.append(
                {
                    "file": file_path,
                    "excerpt": content[:4000],
                }
            )
        return manifests

