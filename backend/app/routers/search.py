"""Search API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    include_projects: bool = True,
    include_documents: bool = True,
    include_proposals: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search across all projects, documents, and proposals."""
    search_service = SearchService(db)
    return await search_service.search_all(
        user_id=current_user.id,
        query=q,
        limit=limit,
        include_projects=include_projects,
        include_documents=include_documents,
        include_proposals=include_proposals,
    )


@router.get("/recent")
async def get_recent(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recently accessed items."""
    search_service = SearchService(db)
    return await search_service.get_recent_items(
        user_id=current_user.id,
        limit=limit,
    )


@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get search suggestions based on partial query."""
    search_service = SearchService(db)
    return await search_service.get_suggestions(
        user_id=current_user.id,
        partial_query=q,
        limit=limit,
    )
