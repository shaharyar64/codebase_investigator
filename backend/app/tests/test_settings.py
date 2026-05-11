"""Tests for database settings."""

from app.core.config.settings import Settings


def test_builds_async_postgres_url_from_db_parts() -> None:
    settings = Settings(
        _env_file=None,
        db_name="codebase_investigator",
        db_user="postgres",
        db_password="secret",
        db_host="localhost",
        db_port=5432,
    )

    assert (
        settings.async_database_url
        == "postgresql+asyncpg://postgres:secret@localhost:5432/"
        "codebase_investigator"
    )


def test_database_url_overrides_db_parts_and_normalizes_driver() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://postgres:secret@db:5432/app",
        db_name="ignored",
        db_user="ignored",
    )

    assert (
        settings.async_database_url
        == "postgresql+asyncpg://postgres:secret@db:5432/app"
    )


def test_repository_root_resolves_relative_to_backend_root() -> None:
    settings = Settings(
        _env_file=None,
        repository_storage_path="../data/repos",
    )

    assert settings.repository_root.name == "repos"
    assert settings.repository_root.parent.name == "data"
    assert settings.repository_root.parent.parent.name == "codebase_investigator"
