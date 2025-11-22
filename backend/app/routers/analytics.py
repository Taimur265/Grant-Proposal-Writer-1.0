"""Analytics API routes."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive dashboard statistics for the current user."""
    analytics = AnalyticsService(db)
    return await analytics.get_user_dashboard_stats(current_user.id)


@router.get("/projects/{project_id}/insights")
async def get_project_insights(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed insights for a specific project."""
    analytics = AnalyticsService(db)
    return await analytics.get_project_insights(project_id)
