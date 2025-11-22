"""Funder and grant opportunity API routes."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.funder import (
    Funder, FunderType, GrantOpportunity, OpportunityStatus,
    GrantApplication, ApplicationStatus
)
from app.routers.auth import get_current_user
from app.services.funder import FunderService, OpportunityMatcher

router = APIRouter(prefix="/funders", tags=["Funders"])


# Schemas
class FunderCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    funder_type: str = "foundation"
    description: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    focus_areas: List[str] = []
    geographic_focus: List[str] = []
    typical_award_min: Optional[float] = None
    typical_award_max: Optional[float] = None
    max_indirect_rate: Optional[float] = None


class OpportunityCreate(BaseModel):
    funder_id: UUID
    title: str
    description: Optional[str] = None
    program_url: Optional[str] = None
    opportunity_number: Optional[str] = None
    award_floor: Optional[float] = None
    award_ceiling: Optional[float] = None
    close_date: Optional[datetime] = None
    eligible_applicants: List[str] = []
    focus_areas: List[str] = []
    required_documents: List[str] = []


class ApplicationCreate(BaseModel):
    opportunity_id: UUID
    project_id: Optional[UUID] = None
    application_title: Optional[str] = None
    requested_amount: Optional[float] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    awarded_amount: Optional[float] = None
    submission_date: Optional[datetime] = None
    confirmation_number: Optional[str] = None
    reviewer_feedback: Optional[str] = None
    score: Optional[float] = None


# Funder endpoints
@router.get("/")
async def list_funders(
    q: Optional[str] = None,
    funder_type: Optional[str] = None,
    min_award: Optional[float] = None,
    max_award: Optional[float] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search and list funders."""
    service = FunderService(db)
    return await service.search_funders(
        query=q,
        funder_type=funder_type,
        min_award=min_award,
        max_award=max_award,
        limit=limit,
        offset=offset,
    )


@router.post("/")
async def create_funder(
    funder_data: FunderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new funder."""
    funder = Funder(
        name=funder_data.name,
        short_name=funder_data.short_name,
        funder_type=FunderType(funder_data.funder_type),
        description=funder_data.description,
        website=funder_data.website,
        email=funder_data.email,
        focus_areas=funder_data.focus_areas,
        geographic_focus=funder_data.geographic_focus,
        typical_award_min=funder_data.typical_award_min,
        typical_award_max=funder_data.typical_award_max,
        max_indirect_rate=funder_data.max_indirect_rate,
        added_by_id=current_user.id,
    )

    db.add(funder)
    await db.commit()
    await db.refresh(funder)

    return {"id": str(funder.id), "name": funder.name}


@router.get("/{funder_id}")
async def get_funder(
    funder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get funder details."""
    funder = await db.get(Funder, funder_id)
    if not funder:
        raise HTTPException(status_code=404, detail="Funder not found")

    return {
        "id": str(funder.id),
        "name": funder.name,
        "short_name": funder.short_name,
        "type": funder.funder_type.value,
        "description": funder.description,
        "website": funder.website,
        "email": funder.email,
        "phone": funder.phone,
        "address": funder.address,
        "focus_areas": funder.focus_areas,
        "geographic_focus": funder.geographic_focus,
        "eligible_organizations": funder.eligible_organizations,
        "typical_award_min": funder.typical_award_min,
        "typical_award_max": funder.typical_award_max,
        "total_annual_giving": funder.total_annual_giving,
        "indirect_cost_policy": funder.indirect_cost_policy,
        "max_indirect_rate": funder.max_indirect_rate,
        "application_requirements": funder.application_requirements,
    }


# Opportunity endpoints
@router.get("/opportunities/search")
async def search_opportunities(
    q: Optional[str] = None,
    status: Optional[str] = None,
    funder_id: Optional[UUID] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    closing_within_days: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search grant opportunities."""
    service = FunderService(db)
    return await service.search_opportunities(
        query=q,
        status=status,
        funder_id=funder_id,
        min_amount=min_amount,
        max_amount=max_amount,
        closing_within_days=closing_within_days,
        limit=limit,
        offset=offset,
    )


@router.post("/opportunities")
async def create_opportunity(
    opp_data: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new grant opportunity."""
    opportunity = GrantOpportunity(
        funder_id=opp_data.funder_id,
        title=opp_data.title,
        description=opp_data.description,
        program_url=opp_data.program_url,
        opportunity_number=opp_data.opportunity_number,
        award_floor=opp_data.award_floor,
        award_ceiling=opp_data.award_ceiling,
        close_date=opp_data.close_date,
        eligible_applicants=opp_data.eligible_applicants,
        focus_areas=opp_data.focus_areas,
        required_documents=opp_data.required_documents,
    )

    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)

    return {"id": str(opportunity.id), "title": opportunity.title}


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get opportunity details."""
    service = FunderService(db)
    details = await service.get_opportunity_details(opportunity_id)
    if not details:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return details


@router.post("/opportunities/{opportunity_id}/bookmark")
async def toggle_bookmark(
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle bookmark on an opportunity."""
    opportunity = await db.get(GrantOpportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opportunity.is_bookmarked = not opportunity.is_bookmarked
    await db.commit()

    return {"bookmarked": opportunity.is_bookmarked}


# Application endpoints
@router.get("/applications")
async def list_applications(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's grant applications."""
    stmt = select(GrantApplication).where(GrantApplication.user_id == current_user.id)

    if status:
        stmt = stmt.where(GrantApplication.status == ApplicationStatus(status))

    stmt = stmt.order_by(GrantApplication.updated_at.desc()).limit(limit)
    result = await db.execute(stmt)

    applications = []
    for app in result.scalars():
        applications.append({
            "id": str(app.id),
            "opportunity_id": str(app.opportunity_id),
            "project_id": str(app.project_id) if app.project_id else None,
            "title": app.application_title,
            "status": app.status.value,
            "requested_amount": app.requested_amount,
            "awarded_amount": app.awarded_amount,
            "submission_date": app.submission_date.isoformat() if app.submission_date else None,
            "created_at": app.created_at.isoformat(),
        })

    return {"applications": applications}


@router.post("/applications")
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new grant application."""
    application = GrantApplication(
        opportunity_id=app_data.opportunity_id,
        project_id=app_data.project_id,
        user_id=current_user.id,
        application_title=app_data.application_title,
        requested_amount=app_data.requested_amount,
    )

    db.add(application)
    await db.commit()
    await db.refresh(application)

    return {"id": str(application.id)}


@router.patch("/applications/{application_id}")
async def update_application(
    application_id: UUID,
    update_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an application."""
    application = await db.get(GrantApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_dict = update_data.dict(exclude_unset=True)
    if "status" in update_dict:
        update_dict["status"] = ApplicationStatus(update_dict["status"])

    for key, value in update_dict.items():
        setattr(application, key, value)

    await db.commit()
    return {"message": "Application updated"}


@router.get("/applications/stats")
async def get_application_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application statistics."""
    service = FunderService(db)
    return await service.get_application_stats(current_user.id)


@router.get("/deadlines")
async def get_upcoming_deadlines(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming grant deadlines."""
    service = FunderService(db)
    deadlines = await service.get_upcoming_deadlines(current_user.id, days)
    return {"deadlines": deadlines}
