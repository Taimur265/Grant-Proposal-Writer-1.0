"""Funder Research and Discovery API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.user import User
from app.models.funder_research import (
    FunderProfile, GrantOpportunity, CultivationActivity,
    FunderType, FitScore
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/funder-research", tags=["Funder Research"])


class FunderProfileCreate(BaseModel):
    name: str
    funder_type: FunderType
    website: Optional[str] = None
    email: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    geographic_focus: Optional[List[str]] = None
    average_grant_size: Optional[float] = None
    grant_range_min: Optional[float] = None
    grant_range_max: Optional[float] = None
    accepts_unsolicited: bool = True
    fit_score: Optional[FitScore] = None
    notes: Optional[str] = None


class GrantOpportunityCreate(BaseModel):
    funder_id: UUID
    opportunity_name: str
    description: Optional[str] = None
    funding_amount_min: Optional[float] = None
    funding_amount_max: Optional[float] = None
    application_deadline: datetime
    loi_deadline: Optional[datetime] = None
    eligibility_criteria: Optional[str] = None
    match_required: bool = False
    match_percentage: Optional[float] = None
    priority_level: str = "medium"


class CultivationActivityCreate(BaseModel):
    funder_id: UUID
    activity_type: str
    activity_name: str
    description: Optional[str] = None
    contact_person: Optional[str] = None
    activity_date: datetime
    outcome: Optional[str] = None
    next_steps: Optional[str] = None
    follow_up_date: Optional[datetime] = None


@router.post("/funders")
async def create_funder_profile(
    data: FunderProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a funder profile."""
    funder = FunderProfile(user_id=current_user.id, **data.dict())
    db.add(funder)
    await db.commit()
    await db.refresh(funder)
    return {"id": str(funder.id), "name": funder.name}


@router.get("/funders")
async def list_funders(
    funder_type: Optional[FunderType] = None,
    fit_score: Optional[FitScore] = None,
    search: Optional[str] = None,
    focus_area: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List funder profiles."""
    stmt = select(FunderProfile).where(
        FunderProfile.user_id == current_user.id,
        FunderProfile.is_active == True
    )

    if funder_type:
        stmt = stmt.where(FunderProfile.funder_type == funder_type)
    if fit_score:
        stmt = stmt.where(FunderProfile.fit_score == fit_score)
    if search:
        stmt = stmt.where(FunderProfile.name.ilike(f"%{search}%"))

    result = await db.execute(stmt.order_by(FunderProfile.name))

    return {
        "funders": [
            {
                "id": str(f.id),
                "name": f.name,
                "funder_type": f.funder_type.value,
                "website": f.website,
                "focus_areas": f.focus_areas,
                "average_grant_size": f.average_grant_size,
                "fit_score": f.fit_score.value if f.fit_score else None,
                "accepts_unsolicited": f.accepts_unsolicited,
            }
            for f in result.scalars()
        ]
    }


@router.get("/funders/{funder_id}")
async def get_funder_profile(
    funder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get funder profile with opportunities and cultivation history."""
    funder = await db.get(FunderProfile, funder_id)
    if not funder or funder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Funder not found")

    opportunities_result = await db.execute(
        select(GrantOpportunity).where(GrantOpportunity.funder_id == funder_id)
    )
    cultivation_result = await db.execute(
        select(CultivationActivity)
        .where(CultivationActivity.funder_id == funder_id)
        .order_by(CultivationActivity.activity_date.desc())
        .limit(10)
    )

    return {
        "id": str(funder.id),
        "name": funder.name,
        "funder_type": funder.funder_type.value,
        "website": funder.website,
        "email": funder.email,
        "phone": funder.phone,
        "primary_contact": funder.primary_contact,
        "program_officer": funder.program_officer,
        "total_annual_giving": funder.total_annual_giving,
        "average_grant_size": funder.average_grant_size,
        "grant_range_min": funder.grant_range_min,
        "grant_range_max": funder.grant_range_max,
        "focus_areas": funder.focus_areas,
        "geographic_focus": funder.geographic_focus,
        "population_focus": funder.population_focus,
        "funding_priorities": funder.funding_priorities,
        "eligibility_requirements": funder.eligibility_requirements,
        "restrictions": funder.restrictions,
        "application_process": funder.application_process,
        "accepts_unsolicited": funder.accepts_unsolicited,
        "loi_required": funder.loi_required,
        "fit_score": funder.fit_score.value if funder.fit_score else None,
        "fit_notes": funder.fit_notes,
        "notes": funder.notes,
        "opportunities": [
            {
                "id": str(o.id),
                "opportunity_name": o.opportunity_name,
                "funding_amount_max": o.funding_amount_max,
                "application_deadline": o.application_deadline.isoformat(),
                "status": o.status,
                "priority_level": o.priority_level,
            }
            for o in opportunities_result.scalars()
        ],
        "cultivation_history": [
            {
                "id": str(c.id),
                "activity_type": c.activity_type,
                "activity_name": c.activity_name,
                "activity_date": c.activity_date.isoformat(),
                "outcome": c.outcome,
            }
            for c in cultivation_result.scalars()
        ],
    }


@router.post("/opportunities")
async def create_grant_opportunity(
    data: GrantOpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a grant opportunity."""
    opportunity = GrantOpportunity(user_id=current_user.id, **data.dict())
    db.add(opportunity)
    await db.commit()
    return {"id": str(opportunity.id)}


@router.get("/opportunities")
async def list_opportunities(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    deadline_within_days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List grant opportunities."""
    stmt = select(GrantOpportunity).where(GrantOpportunity.user_id == current_user.id)

    if status:
        stmt = stmt.where(GrantOpportunity.status == status)
    if priority:
        stmt = stmt.where(GrantOpportunity.priority_level == priority)
    if deadline_within_days:
        from datetime import timedelta
        deadline_date = datetime.utcnow() + timedelta(days=deadline_within_days)
        stmt = stmt.where(GrantOpportunity.application_deadline <= deadline_date)

    result = await db.execute(stmt.order_by(GrantOpportunity.application_deadline))

    return {
        "opportunities": [
            {
                "id": str(o.id),
                "opportunity_name": o.opportunity_name,
                "funder_id": str(o.funder_id),
                "funding_amount_max": o.funding_amount_max,
                "application_deadline": o.application_deadline.isoformat(),
                "status": o.status,
                "priority_level": o.priority_level,
                "fit_score": o.fit_score.value if o.fit_score else None,
            }
            for o in result.scalars()
        ]
    }


@router.post("/cultivation")
async def log_cultivation_activity(
    data: CultivationActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a cultivation activity."""
    activity = CultivationActivity(user_id=current_user.id, **data.dict())
    db.add(activity)
    await db.commit()
    return {"id": str(activity.id)}


@router.get("/types")
async def get_funder_types():
    """Get available funder types."""
    return {
        "funder_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in FunderType
        ],
        "fit_scores": [
            {"value": s.value, "label": s.value.title()}
            for s in FitScore
        ],
        "activity_types": [
            {"value": "meeting", "label": "Meeting"},
            {"value": "call", "label": "Phone Call"},
            {"value": "email", "label": "Email"},
            {"value": "event", "label": "Event"},
            {"value": "site_visit", "label": "Site Visit"},
            {"value": "report", "label": "Report Submission"},
            {"value": "thank_you", "label": "Thank You"},
        ],
    }
