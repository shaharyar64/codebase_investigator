"""Centralized runtime settings."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Codebase Investigator"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"
    openai_audit_model: str = "gpt-5.4-mini"
    openai_max_output_tokens: int = 4000

    database_url: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    repository_storage_path: str = "./data/repos"

    max_file_bytes: int = 250_000
    max_search_results: int = 80
    max_context_files: int = 14
    search_context_window: int = 10
    request_timeout_seconds: int = 120

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Support comma-separated CORS origins in environment files."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def async_database_url(self) -> str:
        """Return an async SQLAlchemy database URL."""
        if self.database_url:
            return self._normalize_database_url(self.database_url)
        if self.db_name and self.db_user:
            return self._build_postgres_url()
        return "sqlite+aiosqlite:///./data/app.db"

    @property
    def repository_root(self) -> Path:
        """Return the repository storage root as an absolute path."""
        path = Path(self.repository_storage_path)
        if path.is_absolute():
            return path
        return (self.backend_root / path).resolve()

    @property
    def backend_root(self) -> Path:
        """Return the backend project directory."""
        return Path(__file__).resolve().parents[3]

    def _normalize_database_url(self, database_url: str) -> str:
        """Normalize sync database URLs to async SQLAlchemy driver URLs."""
        if database_url.startswith("sqlite:///"):
            return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return database_url

    def _build_postgres_url(self) -> str:
        """Build an async Postgres URL from DB_* environment variables."""
        user = quote(self.db_user or "", safe="")
        password = quote(self.db_password or "", safe="")
        database = quote(self.db_name or "", safe="")
        host = self.db_host
        auth = f"{user}:{password}" if self.db_password is not None else user
        return (
            f"postgresql+asyncpg://{auth}@{host}:{self.db_port}/{database}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for dependency injection."""
    return Settings()
