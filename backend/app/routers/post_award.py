"""Post-Award Grant Management API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.post_award import (
    AwardedGrant, ReportingRequirement, GrantExpenditure, GrantModification,
    GrantDeliverable, ImpactStory, GrantStatus, ReportType
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/post-award", tags=["Post-Award Management"])


class AwardedGrantCreate(BaseModel):
    grant_title: str
    funder_name: str
    grant_number: Optional[str] = None
    total_award_amount: float
    award_date: datetime
    project_start_date: datetime
    project_end_date: datetime
    project_id: Optional[UUID] = None
    indirect_cost_rate: Optional[float] = None
    cost_share_required: bool = False
    cost_share_amount: Optional[float] = None
    project_director: Optional[str] = None


class ReportingRequirementCreate(BaseModel):
    grant_id: UUID
    report_type: ReportType
    report_name: str
    frequency: str
    due_date: datetime
    submission_method: Optional[str] = None
    assigned_to: Optional[str] = None


class ExpenditureCreate(BaseModel):
    grant_id: UUID
    budget_category: str
    description: str
    budgeted_amount: float
    spent_amount: float = 0
    fiscal_year: Optional[str] = None
    quarter: Optional[int] = None


class ModificationCreate(BaseModel):
    grant_id: UUID
    modification_type: str
    description: str
    justification: Optional[str] = None
    budget_impact: Optional[float] = None
    timeline_impact_days: Optional[int] = None


class ImpactStoryCreate(BaseModel):
    title: str
    story_type: str
    summary: str
    full_story: Optional[str] = None
    quote: Optional[str] = None
    quote_attribution: Optional[str] = None
    project_id: Optional[UUID] = None
    grant_id: Optional[UUID] = None
    quantitative_impact: Optional[List[dict]] = None
    tags: Optional[List[str]] = None
    suitable_for: Optional[List[str]] = None


@router.post("/grants")
async def create_awarded_grant(
    data: AwardedGrantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an awarded grant record."""
    grant = AwardedGrant(user_id=current_user.id, **data.dict())
    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    return {"id": str(grant.id), "title": grant.grant_title}


@router.get("/grants")
async def list_awarded_grants(
    status: Optional[GrantStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List awarded grants."""
    stmt = select(AwardedGrant).where(AwardedGrant.user_id == current_user.id)
    if status:
        stmt = stmt.where(AwardedGrant.status == status)

    result = await db.execute(stmt.order_by(AwardedGrant.project_end_date))

    return {
        "grants": [
            {
                "id": str(g.id),
                "grant_title": g.grant_title,
                "funder_name": g.funder_name,
                "grant_number": g.grant_number,
                "total_award_amount": g.total_award_amount,
                "amount_received": g.amount_received,
                "project_start_date": g.project_start_date.isoformat(),
                "project_end_date": g.project_end_date.isoformat(),
                "status": g.status.value,
                "days_remaining": (g.project_end_date - datetime.utcnow()).days,
            }
            for g in result.scalars()
        ]
    }


@router.get("/grants/{grant_id}")
async def get_awarded_grant(
    grant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get awarded grant details."""
    grant = await db.get(AwardedGrant, grant_id)
    if not grant or grant.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Grant not found")

    # Get related data
    reports_result = await db.execute(
        select(ReportingRequirement)
        .where(ReportingRequirement.grant_id == grant_id)
        .order_by(ReportingRequirement.due_date)
    )
    expenditures_result = await db.execute(
        select(GrantExpenditure).where(GrantExpenditure.grant_id == grant_id)
    )
    modifications_result = await db.execute(
        select(GrantModification)
        .where(GrantModification.grant_id == grant_id)
        .order_by(GrantModification.request_date.desc())
    )
    deliverables_result = await db.execute(
        select(GrantDeliverable)
        .where(GrantDeliverable.grant_id == grant_id)
        .order_by(GrantDeliverable.due_date)
    )

    # Calculate budget summary
    expenditures = list(expenditures_result.scalars())
    total_budgeted = sum(e.budgeted_amount for e in expenditures)
    total_spent = sum(e.spent_amount for e in expenditures)

    return {
        "id": str(grant.id),
        "grant_title": grant.grant_title,
        "funder_name": grant.funder_name,
        "grant_number": grant.grant_number,
        "cfda_number": grant.cfda_number,
        "total_award_amount": grant.total_award_amount,
        "amount_received": grant.amount_received,
        "indirect_cost_rate": grant.indirect_cost_rate,
        "cost_share_required": grant.cost_share_required,
        "cost_share_amount": grant.cost_share_amount,
        "cost_share_met": grant.cost_share_met,
        "award_date": grant.award_date.isoformat(),
        "project_start_date": grant.project_start_date.isoformat(),
        "project_end_date": grant.project_end_date.isoformat(),
        "funder_contact": grant.funder_contact,
        "program_officer": grant.program_officer,
        "project_director": grant.project_director,
        "status": grant.status.value,
        "special_conditions": grant.special_conditions,
        "compliance_requirements": grant.compliance_requirements,
        "budget_summary": {
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "remaining": total_budgeted - total_spent,
            "burn_rate": (total_spent / total_budgeted * 100) if total_budgeted > 0 else 0,
        },
        "reporting_requirements": [
            {
                "id": str(r.id),
                "report_type": r.report_type.value,
                "report_name": r.report_name,
                "frequency": r.frequency,
                "due_date": r.due_date.isoformat(),
                "status": r.status,
                "assigned_to": r.assigned_to,
            }
            for r in reports_result.scalars()
        ],
        "expenditures": [
            {
                "id": str(e.id),
                "budget_category": e.budget_category,
                "description": e.description,
                "budgeted_amount": e.budgeted_amount,
                "spent_amount": e.spent_amount,
                "remaining": e.budgeted_amount - e.spent_amount,
            }
            for e in expenditures
        ],
        "modifications": [
            {
                "id": str(m.id),
                "modification_type": m.modification_type,
                "description": m.description,
                "status": m.status,
                "request_date": m.request_date.isoformat(),
            }
            for m in modifications_result.scalars()
        ],
        "deliverables": [
            {
                "id": str(d.id),
                "deliverable_name": d.deliverable_name,
                "due_date": d.due_date.isoformat(),
                "status": d.status,
            }
            for d in deliverables_result.scalars()
        ],
    }


@router.post("/reporting-requirements")
async def create_reporting_requirement(
    data: ReportingRequirementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a reporting requirement."""
    requirement = ReportingRequirement(**data.dict())
    db.add(requirement)
    await db.commit()
    return {"id": str(requirement.id)}


@router.patch("/reporting-requirements/{requirement_id}/submit")
async def submit_report(
    requirement_id: UUID,
    confirmation_number: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a report as submitted."""
    requirement = await db.get(ReportingRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    requirement.status = "submitted"
    requirement.submitted_date = datetime.utcnow()
    if confirmation_number:
        requirement.confirmation_number = confirmation_number

    await db.commit()
    return {"message": "Report submitted"}


@router.post("/expenditures")
async def record_expenditure(
    data: ExpenditureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a grant expenditure."""
    expenditure = GrantExpenditure(**data.dict())
    db.add(expenditure)
    await db.commit()
    return {"id": str(expenditure.id)}


@router.post("/modifications")
async def request_modification(
    data: ModificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a grant modification."""
    modification = GrantModification(
        request_date=datetime.utcnow(),
        **data.dict()
    )
    db.add(modification)
    await db.commit()
    return {"id": str(modification.id)}


# Impact Stories
@router.post("/impact-stories")
async def create_impact_story(
    data: ImpactStoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an impact story."""
    story = ImpactStory(user_id=current_user.id, **data.dict())
    db.add(story)
    await db.commit()
    return {"id": str(story.id)}


@router.get("/impact-stories")
async def list_impact_stories(
    story_type: Optional[str] = None,
    project_id: Optional[UUID] = None,
    tags: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List impact stories."""
    stmt = select(ImpactStory).where(
        ImpactStory.user_id == current_user.id,
        ImpactStory.is_active == True
    )

    if story_type:
        stmt = stmt.where(ImpactStory.story_type == story_type)
    if project_id:
        stmt = stmt.where(ImpactStory.project_id == project_id)

    result = await db.execute(stmt.order_by(ImpactStory.created_at.desc()))

    return {
        "stories": [
            {
                "id": str(s.id),
                "title": s.title,
                "story_type": s.story_type,
                "summary": s.summary[:200] + "..." if len(s.summary) > 200 else s.summary,
                "quote": s.quote,
                "tags": s.tags,
                "suitable_for": s.suitable_for,
                "use_count": s.use_count,
                "is_approved": s.is_approved,
            }
            for s in result.scalars()
        ]
    }


@router.get("/dashboard")
async def get_post_award_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get post-award dashboard summary."""
    # Active grants
    grants_result = await db.execute(
        select(AwardedGrant).where(
            AwardedGrant.user_id == current_user.id,
            AwardedGrant.status == GrantStatus.ACTIVE
        )
    )
    active_grants = list(grants_result.scalars())

    # Upcoming reports (next 30 days)
    from datetime import timedelta
    reports_result = await db.execute(
        select(ReportingRequirement).where(
            ReportingRequirement.due_date <= datetime.utcnow() + timedelta(days=30),
            ReportingRequirement.status == "pending"
        )
    )

    # Calculate totals
    total_active_funding = sum(g.total_award_amount for g in active_grants)
    total_received = sum(g.amount_received for g in active_grants)

    return {
        "summary": {
            "active_grants": len(active_grants),
            "total_active_funding": total_active_funding,
            "total_received": total_received,
            "pending_reports": len(list(reports_result.scalars())),
        },
        "upcoming_deadlines": [
            {
                "grant_id": str(g.id),
                "grant_title": g.grant_title,
                "end_date": g.project_end_date.isoformat(),
                "days_remaining": (g.project_end_date - datetime.utcnow()).days,
            }
            for g in active_grants
            if (g.project_end_date - datetime.utcnow()).days <= 90
        ],
    }


@router.get("/types")
async def get_post_award_types():
    """Get available types."""
    return {
        "grant_statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in GrantStatus
        ],
        "report_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in ReportType
        ],
        "modification_types": [
            {"value": "budget_revision", "label": "Budget Revision"},
            {"value": "no_cost_extension", "label": "No-Cost Extension"},
            {"value": "scope_change", "label": "Scope Change"},
            {"value": "key_personnel", "label": "Key Personnel Change"},
            {"value": "carryover", "label": "Carryover Request"},
        ],
        "story_types": [
            {"value": "success_story", "label": "Success Story"},
            {"value": "testimonial", "label": "Testimonial"},
            {"value": "case_study", "label": "Case Study"},
        ],
    }
