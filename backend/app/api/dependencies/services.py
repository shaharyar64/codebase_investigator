"""Service dependency factories."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.auditor.agent import AuditorAgent
from app.agents.investigator.agent import InvestigatorAgent
from app.core.config.settings import Settings, get_settings
from app.database.session import get_db_session
from app.repositories.database.repository_store import RepositoryStore
from app.repositories.database.session_store import SessionStore
from app.services.ai.openai_service import OpenAIService
from app.services.analysis.repository_analyzer import RepositoryAnalyzer
from app.services.repository.cloner import GitRepositoryCloner
from app.services.repository.github_url import GitHubUrlParser
from app.services.repository.repository_service import RepositoryService
from app.services.search.ripgrep_service import RipgrepSearchService
from app.services.session.chat_service import ChatService
from app.services.session.session_service import SessionService


def get_repository_store(
    session: AsyncSession = Depends(get_db_session),
) -> RepositoryStore:
    """Return repository persistence dependency."""
    return RepositoryStore(session)


def get_session_store(
    session: AsyncSession = Depends(get_db_session),
) -> SessionStore:
    """Return session persistence dependency."""
    return SessionStore(session)


def get_openai_service(
    settings: Settings = Depends(get_settings),
) -> OpenAIService:
    """Return OpenAI service dependency."""
    return OpenAIService(settings)


def get_repository_service(
    store: RepositoryStore = Depends(get_repository_store),
    settings: Settings = Depends(get_settings),
) -> RepositoryService:
    """Return repository service dependency."""
    return RepositoryService(
        store=store,
        url_parser=GitHubUrlParser(),
        cloner=GitRepositoryCloner(),
        analyzer=RepositoryAnalyzer(),
        settings=settings,
    )


def get_session_service(
    store: SessionStore = Depends(get_session_store),
) -> SessionService:
    """Return session service dependency."""
    return SessionService(store=store)


def get_chat_service(
    repository_store: RepositoryStore = Depends(get_repository_store),
    session_service: SessionService = Depends(get_session_service),
    ai_service: OpenAIService = Depends(get_openai_service),
    settings: Settings = Depends(get_settings),
) -> ChatService:
    """Return chat orchestration service dependency."""
    search_service = RipgrepSearchService()
    investigator_agent = InvestigatorAgent(
        ai_service=ai_service,
        search_service=search_service,
        settings=settings,
    )
    auditor_agent = AuditorAgent(ai_service=ai_service, settings=settings)
    return ChatService(
        repository_store=repository_store,
        session_service=session_service,
        investigator_agent=investigator_agent,
        auditor_agent=auditor_agent,
    )

