"""Repository API routes."""

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.services import get_repository_service
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.repository.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_repository(
    payload: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    """Submit a public GitHub repository for cloning and indexing."""
    return await service.submit_repository(str(payload.url))


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    limit: int = Query(default=20, ge=1, le=100),
    service: RepositoryService = Depends(get_repository_service),
) -> list[RepositoryResponse]:
    """Return recent repositories."""
    return await service.list_repositories(limit=limit)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    """Return repository details."""
    return await service.get_repository_response(repository_id)

