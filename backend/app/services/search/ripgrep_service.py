"""ripgrep-backed source search service."""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.constants.repository import (
    IGNORED_DIRECTORIES,
    IGNORED_FILE_SUFFIXES,
)
from app.repositories.filesystem.file_system_repository import (
    FileSlice,
    FileSystemRepository,
)


@dataclass(frozen=True)
class SearchHit:
    """A single ripgrep match."""

    file: str
    line: int
    text: str


@dataclass(frozen=True)
class CodeContext:
    """A code excerpt selected for model reasoning."""

    file: str
    start_line: int
    end_line: int
    content: str


class RipgrepSearchService:
    """Search source code using ripgrep with a Python fallback."""

    async def search_many(
        self,
        *,
        file_system: FileSystemRepository,
        queries: list[str],
        max_results: int,
    ) -> list[SearchHit]:
        """Run multiple fixed-string searches and return deduplicated hits."""
        hits: list[SearchHit] = []
        seen: set[tuple[str, int, str]] = set()

        for query in self._clean_queries(queries):
            query_hits = await self.search(
                file_system=file_system,
                query=query,
                max_results=max_results,
            )
            for hit in query_hits:
                key = (hit.file, hit.line, hit.text)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(hit)
                if len(hits) >= max_results:
                    return hits
        return hits

    async def search(
        self,
        *,
        file_system: FileSystemRepository,
        query: str,
        max_results: int,
    ) -> list[SearchHit]:
        """Search for a fixed string query."""
        if not query.strip():
            return []
        if shutil.which("rg"):
            return await self._search_with_ripgrep(
                file_system=file_system,
                query=query,
                max_results=max_results,
            )
        return self._search_with_python(
            file_system=file_system,
            query=query,
            max_results=max_results,
        )

    def build_contexts(
        self,
        *,
        file_system: FileSystemRepository,
        hits: list[SearchHit],
        window: int,
        max_contexts: int,
    ) -> list[CodeContext]:
        """Expand search hits into merged file excerpts."""
        contexts: list[CodeContext] = []
        grouped: dict[str, list[int]] = {}
        for hit in hits:
            grouped.setdefault(hit.file, []).append(hit.line)

        for file_path, lines in grouped.items():
            merged_ranges = self._merge_ranges(lines=sorted(lines), window=window)
            for start_line, end_line in merged_ranges:
                try:
                    file_slice = file_system.read_slice(file_path, start_line, end_line)
                except Exception:
                    continue
                contexts.append(self._to_context(file_slice))
                if len(contexts) >= max_contexts:
                    return contexts
        return contexts

    def read_candidate_files(
        self,
        *,
        file_system: FileSystemRepository,
        file_paths: list[str],
        max_contexts: int,
    ) -> list[CodeContext]:
        """Read likely files selected by the planner when they exist."""
        contexts: list[CodeContext] = []
        for file_path in file_paths:
            if len(contexts) >= max_contexts:
                break
            if not file_system.file_exists(file_path):
                continue
            try:
                file_slice = file_system.read_slice(file_path, 1, 220)
            except Exception:
                continue
            contexts.append(self._to_context(file_slice))
        return contexts

    async def _search_with_ripgrep(
        self,
        *,
        file_system: FileSystemRepository,
        query: str,
        max_results: int,
    ) -> list[SearchHit]:
        args = [
            "rg",
            "--json",
            "--line-number",
            "--column",
            "--smart-case",
            "--fixed-strings",
            "--hidden",
            "--no-messages",
            "--max-count",
            str(max_results),
        ]
        for directory in IGNORED_DIRECTORIES:
            args.extend(["--glob", f"!{directory}/**"])
        for suffix in IGNORED_FILE_SUFFIXES:
            args.extend(["--glob", f"!*{suffix}"])
        args.extend([query, str(file_system.root_path)])

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode not in (0, 1):
            return []

        hits: list[SearchHit] = []
        for raw_line in stdout.decode("utf-8", errors="ignore").splitlines():
            if len(hits) >= max_results:
                break
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if payload.get("type") != "match":
                continue
            data = payload.get("data", {})
            path_text = data.get("path", {}).get("text", "")
            line_text = data.get("lines", {}).get("text", "").rstrip()
            line_number = int(data.get("line_number", 0))
            relative = self._relative_to_root(path_text, file_system.root_path)
            hits.append(SearchHit(file=relative, line=line_number, text=line_text))
        return hits

    def _search_with_python(
        self,
        *,
        file_system: FileSystemRepository,
        query: str,
        max_results: int,
    ) -> list[SearchHit]:
        normalized_query = query.lower()
        hits: list[SearchHit] = []
        for entry in file_system.list_files():
            if len(hits) >= max_results:
                break
            try:
                lines = file_system.read_text(entry.path).splitlines()
            except Exception:
                continue
            for index, line in enumerate(lines, start=1):
                if normalized_query in line.lower():
                    hits.append(SearchHit(file=entry.path, line=index, text=line))
                    if len(hits) >= max_results:
                        break
        return hits

    def _clean_queries(self, queries: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for query in queries:
            normalized = query.strip()
            if not normalized or normalized.lower() in seen:
                continue
            seen.add(normalized.lower())
            cleaned.append(normalized)
        return cleaned

    def _merge_ranges(
        self,
        *,
        lines: list[int],
        window: int,
    ) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        for line in lines:
            start_line = max(1, line - window)
            end_line = line + window
            if not ranges or start_line > ranges[-1][1] + 1:
                ranges.append((start_line, end_line))
                continue
            previous_start, previous_end = ranges[-1]
            ranges[-1] = (previous_start, max(previous_end, end_line))
        return ranges

    def _relative_to_root(self, path_text: str, root_path: Path) -> str:
        path = Path(path_text)
        try:
            return path.resolve().relative_to(root_path).as_posix()
        except ValueError:
            return path.as_posix()

    def _to_context(self, file_slice: FileSlice) -> CodeContext:
        return CodeContext(
            file=file_slice.file,
            start_line=file_slice.start_line,
            end_line=file_slice.end_line,
            content=file_slice.content,
        )

