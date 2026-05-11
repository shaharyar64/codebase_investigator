"""Tests for GitHub URL parsing."""

import pytest

from app.services.repository.github_url import GitHubUrlParser
from app.utils.exceptions import RepositoryException


def test_parse_normalizes_github_url() -> None:
    parser = GitHubUrlParser()

    parsed = parser.parse("https://github.com/openai/openai-python")

    assert parsed.owner == "openai"
    assert parsed.name == "openai-python"
    assert parsed.url == "https://github.com/openai/openai-python.git"


def test_parse_rejects_non_github_url() -> None:
    parser = GitHubUrlParser()

    with pytest.raises(RepositoryException):
        parser.parse("https://example.com/openai/openai-python")

