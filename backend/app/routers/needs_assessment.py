"""Needs Assessment API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.needs_assessment import (
    NeedsAssessment, IdentifiedNeed, DataSource, CommunityAsset,
    AssessmentType, DataCollectionMethod
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/needs-assessments", tags=["Needs Assessment"])


# Schemas
class NeedsAssessmentCreate(BaseModel):
    title: str
    assessment_type: AssessmentType
    description: Optional[str] = None
    geographic_area: Optional[str] = None
    target_population: Optional[str] = None
    population_size: Optional[int] = None
    project_id: Optional[UUID] = None


class IdentifiedNeedCreate(BaseModel):
    assessment_id: UUID
    need_statement: str
    category: Optional[str] = None
    priority: str = "medium"
    severity_score: Optional[int] = None
    affected_population: Optional[str] = None
    affected_count: Optional[int] = None
    current_services: Optional[str] = None
    service_gaps: Optional[str] = None
    evidence: Optional[str] = None
    proposed_solution: Optional[str] = None


class DataSourceCreate(BaseModel):
    assessment_id: UUID
    source_name: str
    source_type: str
    collection_method: DataCollectionMethod
    description: Optional[str] = None
    sample_size: Optional[int] = None


class CommunityAssetCreate(BaseModel):
    assessment_id: UUID
    asset_name: str
    asset_type: str
    description: Optional[str] = None
    potential_contribution: Optional[str] = None
    partnership_interest: bool = False


# Assessment CRUD
@router.post("/")
async def create_assessment(
    data: NeedsAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new needs assessment."""
    assessment = NeedsAssessment(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return {"id": str(assessment.id), "title": assessment.title}


@router.get("/")
async def list_assessments(
    assessment_type: Optional[AssessmentType] = None,
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List needs assessments."""
    stmt = select(NeedsAssessment).where(NeedsAssessment.user_id == current_user.id)

    if assessment_type:
        stmt = stmt.where(NeedsAssessment.assessment_type == assessment_type)
    if project_id:
        stmt = stmt.where(NeedsAssessment.project_id == project_id)
    if status:
        stmt = stmt.where(NeedsAssessment.status == status)

    result = await db.execute(stmt.order_by(NeedsAssessment.created_at.desc()))

    return {
        "assessments": [
            {
                "id": str(a.id),
                "title": a.title,
                "assessment_type": a.assessment_type.value,
                "geographic_area": a.geographic_area,
                "target_population": a.target_population,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in result.scalars()
        ]
    }


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get assessment details with all related data."""
    assessment = await db.get(NeedsAssessment, assessment_id)
    if not assessment or assessment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get related data
    needs_result = await db.execute(
        select(IdentifiedNeed).where(IdentifiedNeed.assessment_id == assessment_id)
    )
    sources_result = await db.execute(
        select(DataSource).where(DataSource.assessment_id == assessment_id)
    )
    assets_result = await db.execute(
        select(CommunityAsset).where(CommunityAsset.assessment_id == assessment_id)
    )

    return {
        "id": str(assessment.id),
        "title": assessment.title,
        "assessment_type": assessment.assessment_type.value,
        "description": assessment.description,
        "geographic_area": assessment.geographic_area,
        "target_population": assessment.target_population,
        "population_size": assessment.population_size,
        "data_collection_methods": assessment.data_collection_methods,
        "executive_summary": assessment.executive_summary,
        "key_findings": assessment.key_findings,
        "recommendations": assessment.recommendations,
        "status": assessment.status,
        "identified_needs": [
            {
                "id": str(n.id),
                "need_statement": n.need_statement,
                "category": n.category,
                "priority": n.priority,
                "severity_score": n.severity_score,
                "affected_population": n.affected_population,
                "proposed_solution": n.proposed_solution,
            }
            for n in needs_result.scalars()
        ],
        "data_sources": [
            {
                "id": str(s.id),
                "source_name": s.source_name,
                "source_type": s.source_type,
                "collection_method": s.collection_method.value,
                "sample_size": s.sample_size,
            }
            for s in sources_result.scalars()
        ],
        "community_assets": [
            {
                "id": str(a.id),
                "asset_name": a.asset_name,
                "asset_type": a.asset_type,
                "potential_contribution": a.potential_contribution,
                "partnership_interest": a.partnership_interest,
            }
            for a in assets_result.scalars()
        ],
    }


# Identified Needs
@router.post("/needs")
async def add_identified_need(
    data: IdentifiedNeedCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an identified need to an assessment."""
    need = IdentifiedNeed(**data.dict())
    db.add(need)
    await db.commit()
    return {"id": str(need.id)}


@router.delete("/needs/{need_id}")
async def delete_identified_need(
    need_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an identified need."""
    need = await db.get(IdentifiedNeed, need_id)
    if need:
        await db.delete(need)
        await db.commit()
    return {"message": "Need deleted"}


# Data Sources
@router.post("/data-sources")
async def add_data_source(
    data: DataSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a data source to an assessment."""
    source = DataSource(**data.dict())
    db.add(source)
    await db.commit()
    return {"id": str(source.id)}


# Community Assets
@router.post("/community-assets")
async def add_community_asset(
    data: CommunityAssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a community asset to an assessment."""
    asset = CommunityAsset(**data.dict())
    db.add(asset)
    await db.commit()
    return {"id": str(asset.id)}


@router.get("/types")
async def get_assessment_types():
    """Get available assessment types."""
    return {
        "assessment_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in AssessmentType
        ],
        "data_collection_methods": [
            {"value": m.value, "label": m.value.replace("_", " ").title()}
            for m in DataCollectionMethod
        ],
        "need_categories": [
            "health", "education", "economic", "housing", "food_security",
            "transportation", "childcare", "employment", "safety", "environment", "other"
        ],
        "asset_types": [
            "individual", "organizational", "institutional", "physical", "economic"
        ],
    }
