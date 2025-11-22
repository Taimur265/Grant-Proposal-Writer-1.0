"""Risk assessment and management API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.risk import Risk, RiskMitigation, RiskReview, RiskCategory, RiskLikelihood, RiskImpact, RiskStatus
from app.routers.auth import get_current_user

router = APIRouter(prefix="/risks", tags=["Risk Management"])

# Likelihood and impact scores for calculation
LIKELIHOOD_SCORES = {
    RiskLikelihood.RARE: 1,
    RiskLikelihood.UNLIKELY: 2,
    RiskLikelihood.POSSIBLE: 3,
    RiskLikelihood.LIKELY: 4,
    RiskLikelihood.ALMOST_CERTAIN: 5,
}

IMPACT_SCORES = {
    RiskImpact.INSIGNIFICANT: 1,
    RiskImpact.MINOR: 2,
    RiskImpact.MODERATE: 3,
    RiskImpact.MAJOR: 4,
    RiskImpact.CATASTROPHIC: 5,
}


# Schemas
class RiskCreate(BaseModel):
    project_id: UUID
    title: str
    description: str
    category: RiskCategory
    likelihood: RiskLikelihood
    impact: RiskImpact
    owner_name: Optional[str] = None
    triggers: Optional[List[str]] = None
    potential_cost: Optional[float] = None


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RiskCategory] = None
    likelihood: Optional[RiskLikelihood] = None
    impact: Optional[RiskImpact] = None
    status: Optional[RiskStatus] = None
    owner_name: Optional[str] = None
    triggers: Optional[List[str]] = None
    notes: Optional[str] = None


class MitigationCreate(BaseModel):
    risk_id: UUID
    strategy_type: str  # avoid, transfer, mitigate, accept
    description: str
    actions: List[dict] = []
    responsible_person: Optional[str] = None
    target_completion: Optional[datetime] = None
    cost: Optional[float] = None


class ReviewCreate(BaseModel):
    risk_id: UUID
    review_date: datetime
    findings: str
    new_likelihood: Optional[str] = None
    new_impact: Optional[str] = None
    new_status: Optional[str] = None
    recommendations: Optional[str] = None
    next_review_date: Optional[datetime] = None


# Risk endpoints
@router.post("/")
async def create_risk(
    data: RiskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new risk."""
    risk_score = LIKELIHOOD_SCORES[data.likelihood] * IMPACT_SCORES[data.impact]

    risk = Risk(
        user_id=current_user.id,
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        category=data.category,
        likelihood=data.likelihood,
        impact=data.impact,
        risk_score=risk_score,
        owner_name=data.owner_name,
        triggers=data.triggers,
        potential_cost=data.potential_cost,
    )
    db.add(risk)
    await db.commit()
    await db.refresh(risk)
    return {"id": str(risk.id), "risk_score": risk_score}


@router.get("/")
async def list_risks(
    project_id: Optional[UUID] = None,
    category: Optional[RiskCategory] = None,
    status: Optional[RiskStatus] = None,
    min_score: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List risks with filtering."""
    stmt = select(Risk).where(
        Risk.user_id == current_user.id,
        Risk.is_active == True
    )

    if project_id:
        stmt = stmt.where(Risk.project_id == project_id)
    if category:
        stmt = stmt.where(Risk.category == category)
    if status:
        stmt = stmt.where(Risk.status == status)
    if min_score:
        stmt = stmt.where(Risk.risk_score >= min_score)

    result = await db.execute(stmt.order_by(Risk.risk_score.desc()))

    return {
        "risks": [
            {
                "id": str(r.id),
                "title": r.title,
                "category": r.category.value,
                "likelihood": r.likelihood.value,
                "impact": r.impact.value,
                "risk_score": r.risk_score,
                "status": r.status.value,
                "owner_name": r.owner_name,
            }
            for r in result.scalars()
        ]
    }


@router.get("/{risk_id}")
async def get_risk(
    risk_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk details."""
    risk = await db.get(Risk, risk_id)
    if not risk or risk.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Risk not found")

    # Get mitigations
    mit_result = await db.execute(
        select(RiskMitigation).where(RiskMitigation.risk_id == risk_id)
    )

    # Get reviews
    rev_result = await db.execute(
        select(RiskReview)
        .where(RiskReview.risk_id == risk_id)
        .order_by(RiskReview.review_date.desc())
    )

    return {
        "id": str(risk.id),
        "title": risk.title,
        "description": risk.description,
        "category": risk.category.value,
        "status": risk.status.value,
        "likelihood": risk.likelihood.value,
        "impact": risk.impact.value,
        "risk_score": risk.risk_score,
        "owner_name": risk.owner_name,
        "identified_date": risk.identified_date.isoformat(),
        "triggers": risk.triggers,
        "early_warning_indicators": risk.early_warning_indicators,
        "potential_cost": risk.potential_cost,
        "notes": risk.notes,
        "mitigations": [
            {
                "id": str(m.id),
                "strategy_type": m.strategy_type,
                "description": m.description,
                "status": m.status,
                "actions": m.actions,
            }
            for m in mit_result.scalars()
        ],
        "reviews": [
            {
                "id": str(r.id),
                "review_date": r.review_date.isoformat(),
                "findings": r.findings,
                "recommendations": r.recommendations,
            }
            for r in rev_result.scalars()
        ],
    }


@router.patch("/{risk_id}")
async def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a risk."""
    risk = await db.get(Risk, risk_id)
    if not risk or risk.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Risk not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(risk, key, value)

    # Recalculate score if likelihood or impact changed
    if data.likelihood or data.impact:
        risk.risk_score = LIKELIHOOD_SCORES[risk.likelihood] * IMPACT_SCORES[risk.impact]

    await db.commit()
    return {"message": "Risk updated", "risk_score": risk.risk_score}


@router.delete("/{risk_id}")
async def delete_risk(
    risk_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a risk."""
    risk = await db.get(Risk, risk_id)
    if not risk or risk.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Risk not found")

    risk.is_active = False
    await db.commit()
    return {"message": "Risk deleted"}


# Mitigation endpoints
@router.post("/mitigations")
async def create_mitigation(
    data: MitigationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a mitigation strategy."""
    mitigation = RiskMitigation(**data.dict())
    db.add(mitigation)

    # Update risk status
    risk = await db.get(Risk, data.risk_id)
    if risk and risk.status == RiskStatus.IDENTIFIED:
        risk.status = RiskStatus.MITIGATING

    await db.commit()
    return {"id": str(mitigation.id)}


@router.patch("/mitigations/{mitigation_id}")
async def update_mitigation(
    mitigation_id: UUID,
    status: str,
    effectiveness_rating: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update mitigation status."""
    mitigation = await db.get(RiskMitigation, mitigation_id)
    if not mitigation:
        raise HTTPException(status_code=404, detail="Mitigation not found")

    mitigation.status = status
    if effectiveness_rating:
        mitigation.effectiveness_rating = effectiveness_rating
    if status == "completed":
        mitigation.actual_completion = datetime.utcnow()

    await db.commit()
    return {"message": "Mitigation updated"}


# Review endpoints
@router.post("/reviews")
async def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a risk review."""
    review = RiskReview(
        reviewer_id=current_user.id,
        **data.dict()
    )
    db.add(review)

    # Update risk if assessment changed
    risk = await db.get(Risk, data.risk_id)
    if risk:
        risk.review_date = data.review_date
        if data.new_status:
            risk.status = RiskStatus(data.new_status)

    await db.commit()
    return {"id": str(review.id)}


# Analysis endpoints
@router.get("/matrix")
async def get_risk_matrix(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk matrix data."""
    stmt = select(Risk).where(
        Risk.user_id == current_user.id,
        Risk.is_active == True
    )
    if project_id:
        stmt = stmt.where(Risk.project_id == project_id)

    result = await db.execute(stmt)

    # Build matrix
    matrix = {}
    for l in RiskLikelihood:
        for i in RiskImpact:
            key = f"{l.value}_{i.value}"
            matrix[key] = []

    for risk in result.scalars():
        key = f"{risk.likelihood.value}_{risk.impact.value}"
        matrix[key].append({
            "id": str(risk.id),
            "title": risk.title,
            "score": risk.risk_score,
        })

    return {
        "matrix": matrix,
        "likelihood_levels": [l.value for l in RiskLikelihood],
        "impact_levels": [i.value for i in RiskImpact],
    }


@router.get("/summary")
async def get_risk_summary(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk summary statistics."""
    stmt = select(Risk).where(
        Risk.user_id == current_user.id,
        Risk.is_active == True
    )
    if project_id:
        stmt = stmt.where(Risk.project_id == project_id)

    result = await db.execute(stmt)
    risks = list(result.scalars())

    # Count by category
    by_category = {}
    for cat in RiskCategory:
        by_category[cat.value] = sum(1 for r in risks if r.category == cat)

    # Count by status
    by_status = {}
    for status in RiskStatus:
        by_status[status.value] = sum(1 for r in risks if r.status == status)

    # High risks
    high_risks = [r for r in risks if r.risk_score >= 15]

    return {
        "total_risks": len(risks),
        "high_risk_count": len(high_risks),
        "by_category": by_category,
        "by_status": by_status,
        "avg_risk_score": sum(r.risk_score for r in risks) / len(risks) if risks else 0,
        "high_risks": [
            {
                "id": str(r.id),
                "title": r.title,
                "score": r.risk_score,
                "category": r.category.value,
            }
            for r in sorted(high_risks, key=lambda x: x.risk_score, reverse=True)[:5]
        ],
    }


@router.get("/categories")
async def get_risk_categories():
    """Get available risk categories and levels."""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in RiskCategory
        ],
        "likelihood_levels": [
            {"value": l.value, "label": l.value.replace("_", " ").title(), "score": LIKELIHOOD_SCORES[l]}
            for l in RiskLikelihood
        ],
        "impact_levels": [
            {"value": i.value, "label": i.value.replace("_", " ").title(), "score": IMPACT_SCORES[i]}
            for i in RiskImpact
        ],
        "statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in RiskStatus
        ],
    }
