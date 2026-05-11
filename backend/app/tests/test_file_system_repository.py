"""Tests for safe repository file access."""

import pytest

from app.repositories.filesystem.file_system_repository import FileSystemRepository
from app.utils.exceptions import RepositoryException


def test_read_slice_returns_inclusive_line_range(tmp_path) -> None:
    source_file = tmp_path / "app.py"
    source_file.write_text("one\ntwo\nthree\n", encoding="utf-8")
    repository = FileSystemRepository(tmp_path, max_file_bytes=10_000)

    file_slice = repository.read_slice("app.py", 2, 3)

    assert file_slice.content == "two\nthree"
    assert file_slice.start_line == 2
    assert file_slice.end_line == 3


def test_safe_path_rejects_escape(tmp_path) -> None:
    repository = FileSystemRepository(tmp_path, max_file_bytes=10_000)

    with pytest.raises(RepositoryException):
        repository.read_text("../outside.py")

