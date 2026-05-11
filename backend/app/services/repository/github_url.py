"""GitHub URL parsing and normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.exceptions import RepositoryException

GITHUB_REPOSITORY_PATTERN = re.compile(
    r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<name>[\w.-]+?)(?:\.git)?/?$"
)


@dataclass(frozen=True)
class GitHubRepositoryUrl:
    """Normalized public GitHub repository URL parts."""

    owner: str
    name: str
    url: str


class GitHubUrlParser:
    """Validate and normalize GitHub repository URLs."""

    def parse(self, raw_url: str) -> GitHubRepositoryUrl:
        """Parse a GitHub repository URL."""
        match = GITHUB_REPOSITORY_PATTERN.match(raw_url.strip())
        if not match:
            raise RepositoryException(
                "Only public GitHub repository URLs are supported."
            )

        owner = match.group("owner")
        name = match.group("name").removesuffix(".git")
        normalized_url = f"https://github.com/{owner}/{name}.git"
        return GitHubRepositoryUrl(owner=owner, name=name, url=normalized_url)

