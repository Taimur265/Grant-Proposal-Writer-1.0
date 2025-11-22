"""Stakeholder management API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.user import User
from app.models.stakeholder import (
    Stakeholder, StakeholderInteraction, StakeholderCommitment,
    StakeholderType, EngagementLevel
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/stakeholders", tags=["Stakeholders"])


# Schemas
class StakeholderCreate(BaseModel):
    name: str
    organization: Optional[str] = None
    title: Optional[str] = None
    stakeholder_type: StakeholderType
    email: Optional[str] = None
    phone: Optional[str] = None
    engagement_level: EngagementLevel = EngagementLevel.MEDIUM
    influence_level: str = "medium"
    interest_level: str = "medium"
    project_id: Optional[UUID] = None
    interests: Optional[List[str]] = None
    needs: Optional[List[str]] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class StakeholderUpdate(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    engagement_level: Optional[EngagementLevel] = None
    influence_level: Optional[str] = None
    interest_level: Optional[str] = None
    relationship_status: Optional[str] = None
    relationship_notes: Optional[str] = None
    interests: Optional[List[str]] = None
    needs: Optional[List[str]] = None
    notes: Optional[str] = None


class InteractionCreate(BaseModel):
    stakeholder_id: UUID
    interaction_type: str
    subject: str
    description: Optional[str] = None
    interaction_date: datetime
    duration_minutes: Optional[int] = None
    outcome: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class CommitmentCreate(BaseModel):
    stakeholder_id: UUID
    project_id: Optional[UUID] = None
    commitment_type: str
    description: str
    amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Stakeholder endpoints
@router.post("/")
async def create_stakeholder(
    data: StakeholderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new stakeholder."""
    stakeholder = Stakeholder(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(stakeholder)
    await db.commit()
    await db.refresh(stakeholder)
    return {"id": str(stakeholder.id), "name": stakeholder.name}


@router.get("/")
async def list_stakeholders(
    stakeholder_type: Optional[StakeholderType] = None,
    project_id: Optional[UUID] = None,
    engagement_level: Optional[EngagementLevel] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List stakeholders with filtering."""
    stmt = select(Stakeholder).where(
        Stakeholder.user_id == current_user.id,
        Stakeholder.is_active == True
    )

    if stakeholder_type:
        stmt = stmt.where(Stakeholder.stakeholder_type == stakeholder_type)
    if project_id:
        stmt = stmt.where(Stakeholder.project_id == project_id)
    if engagement_level:
        stmt = stmt.where(Stakeholder.engagement_level == engagement_level)
    if search:
        stmt = stmt.where(
            Stakeholder.name.ilike(f"%{search}%") |
            Stakeholder.organization.ilike(f"%{search}%")
        )

    result = await db.execute(stmt.order_by(Stakeholder.name))

    stakeholders = []
    for s in result.scalars():
        stakeholders.append({
            "id": str(s.id),
            "name": s.name,
            "organization": s.organization,
            "title": s.title,
            "stakeholder_type": s.stakeholder_type.value,
            "email": s.email,
            "engagement_level": s.engagement_level.value,
            "influence_level": s.influence_level,
            "interest_level": s.interest_level,
            "relationship_status": s.relationship_status,
            "tags": s.tags,
        })

    return {"stakeholders": stakeholders, "total": len(stakeholders)}


@router.get("/{stakeholder_id}")
async def get_stakeholder(
    stakeholder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get stakeholder details."""
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if not stakeholder or stakeholder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get recent interactions
    interactions_result = await db.execute(
        select(StakeholderInteraction)
        .where(StakeholderInteraction.stakeholder_id == stakeholder_id)
        .order_by(StakeholderInteraction.interaction_date.desc())
        .limit(5)
    )

    # Get commitments
    commitments_result = await db.execute(
        select(StakeholderCommitment)
        .where(StakeholderCommitment.stakeholder_id == stakeholder_id)
    )

    return {
        "id": str(stakeholder.id),
        "name": stakeholder.name,
        "organization": stakeholder.organization,
        "title": stakeholder.title,
        "stakeholder_type": stakeholder.stakeholder_type.value,
        "email": stakeholder.email,
        "phone": stakeholder.phone,
        "address": stakeholder.address,
        "engagement_level": stakeholder.engagement_level.value,
        "influence_level": stakeholder.influence_level,
        "interest_level": stakeholder.interest_level,
        "relationship_status": stakeholder.relationship_status,
        "relationship_notes": stakeholder.relationship_notes,
        "interests": stakeholder.interests,
        "needs": stakeholder.needs,
        "expectations": stakeholder.expectations,
        "last_contact_date": stakeholder.last_contact_date.isoformat() if stakeholder.last_contact_date else None,
        "next_contact_date": stakeholder.next_contact_date.isoformat() if stakeholder.next_contact_date else None,
        "notes": stakeholder.notes,
        "tags": stakeholder.tags,
        "recent_interactions": [
            {
                "id": str(i.id),
                "type": i.interaction_type,
                "subject": i.subject,
                "date": i.interaction_date.isoformat(),
            }
            for i in interactions_result.scalars()
        ],
        "commitments": [
            {
                "id": str(c.id),
                "type": c.commitment_type,
                "description": c.description,
                "amount": c.amount,
                "status": c.status,
            }
            for c in commitments_result.scalars()
        ],
    }


@router.patch("/{stakeholder_id}")
async def update_stakeholder(
    stakeholder_id: UUID,
    data: StakeholderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a stakeholder."""
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if not stakeholder or stakeholder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(stakeholder, key, value)

    await db.commit()
    return {"message": "Stakeholder updated"}


@router.delete("/{stakeholder_id}")
async def delete_stakeholder(
    stakeholder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a stakeholder."""
    stakeholder = await db.get(Stakeholder, stakeholder_id)
    if not stakeholder or stakeholder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    stakeholder.is_active = False
    await db.commit()
    return {"message": "Stakeholder deleted"}


# Interaction endpoints
@router.post("/interactions")
async def create_interaction(
    data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log an interaction with a stakeholder."""
    interaction = StakeholderInteraction(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(interaction)

    # Update last contact date
    stakeholder = await db.get(Stakeholder, data.stakeholder_id)
    if stakeholder:
        stakeholder.last_contact_date = data.interaction_date

    await db.commit()
    return {"id": str(interaction.id)}


@router.get("/interactions/{stakeholder_id}")
async def list_interactions(
    stakeholder_id: UUID,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List interactions for a stakeholder."""
    result = await db.execute(
        select(StakeholderInteraction)
        .where(StakeholderInteraction.stakeholder_id == stakeholder_id)
        .order_by(StakeholderInteraction.interaction_date.desc())
        .limit(limit)
    )

    return {
        "interactions": [
            {
                "id": str(i.id),
                "type": i.interaction_type,
                "subject": i.subject,
                "description": i.description,
                "date": i.interaction_date.isoformat(),
                "duration_minutes": i.duration_minutes,
                "outcome": i.outcome,
                "follow_up_required": i.follow_up_required,
            }
            for i in result.scalars()
        ]
    }


# Commitment endpoints
@router.post("/commitments")
async def create_commitment(
    data: CommitmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a stakeholder commitment."""
    commitment = StakeholderCommitment(**data.dict())
    db.add(commitment)
    await db.commit()
    return {"id": str(commitment.id)}


@router.get("/matrix")
async def get_stakeholder_matrix(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get stakeholder analysis matrix (influence vs interest)."""
    stmt = select(Stakeholder).where(
        Stakeholder.user_id == current_user.id,
        Stakeholder.is_active == True
    )
    if project_id:
        stmt = stmt.where(Stakeholder.project_id == project_id)

    result = await db.execute(stmt)

    # Organize by quadrant
    matrix = {
        "high_influence_high_interest": [],  # Key players - engage closely
        "high_influence_low_interest": [],   # Keep satisfied
        "low_influence_high_interest": [],   # Keep informed
        "low_influence_low_interest": [],    # Monitor
    }

    for s in result.scalars():
        quadrant = f"{'high' if s.influence_level == 'high' else 'low'}_influence_{'high' if s.interest_level == 'high' else 'low'}_interest"
        matrix[quadrant].append({
            "id": str(s.id),
            "name": s.name,
            "organization": s.organization,
            "type": s.stakeholder_type.value,
        })

    return {"matrix": matrix}


@router.get("/types")
async def get_stakeholder_types():
    """Get available stakeholder types."""
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in StakeholderType
        ],
        "engagement_levels": [
            {"value": e.value, "label": e.value.title()}
            for e in EngagementLevel
        ],
    }
