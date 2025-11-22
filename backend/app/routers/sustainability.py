"""Sustainability Planning API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.sustainability import SustainabilityPlan, FundingStrategy, CapacityElement, FundingSource
from app.routers.auth import get_current_user

router = APIRouter(prefix="/sustainability", tags=["Sustainability Planning"])


class SustainabilityPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    sustainability_vision: Optional[str] = None
    project_id: Optional[UUID] = None
    current_annual_budget: Optional[float] = None
    grant_end_date: Optional[datetime] = None


class FundingStrategyCreate(BaseModel):
    sustainability_plan_id: UUID
    funding_source: FundingSource
    strategy_name: str
    description: Optional[str] = None
    current_amount: Optional[float] = None
    year_1_target: Optional[float] = None
    year_2_target: Optional[float] = None
    year_3_target: Optional[float] = None
    key_activities: Optional[List[str]] = None
    responsible_person: Optional[str] = None


class CapacityElementCreate(BaseModel):
    sustainability_plan_id: UUID
    element_type: str
    element_name: str
    description: Optional[str] = None
    current_status: Optional[str] = None
    target_status: Optional[str] = None
    resources_needed: Optional[str] = None
    estimated_cost: Optional[float] = None


@router.post("/plans")
async def create_sustainability_plan(
    data: SustainabilityPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a sustainability plan."""
    plan = SustainabilityPlan(user_id=current_user.id, **data.dict())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"id": str(plan.id), "title": plan.title}


@router.get("/plans")
async def list_sustainability_plans(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List sustainability plans."""
    stmt = select(SustainabilityPlan).where(SustainabilityPlan.user_id == current_user.id)
    if project_id:
        stmt = stmt.where(SustainabilityPlan.project_id == project_id)

    result = await db.execute(stmt.order_by(SustainabilityPlan.created_at.desc()))

    return {
        "plans": [
            {
                "id": str(p.id),
                "title": p.title,
                "sustainability_vision": p.sustainability_vision,
                "grant_end_date": p.grant_end_date.isoformat() if p.grant_end_date else None,
                "status": p.status,
            }
            for p in result.scalars()
        ]
    }


@router.get("/plans/{plan_id}")
async def get_sustainability_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sustainability plan details."""
    plan = await db.get(SustainabilityPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")

    strategies_result = await db.execute(
        select(FundingStrategy).where(FundingStrategy.sustainability_plan_id == plan_id)
    )
    capacity_result = await db.execute(
        select(CapacityElement).where(CapacityElement.sustainability_plan_id == plan_id)
    )

    return {
        "id": str(plan.id),
        "title": plan.title,
        "description": plan.description,
        "sustainability_vision": plan.sustainability_vision,
        "long_term_goals": plan.long_term_goals,
        "current_annual_budget": plan.current_annual_budget,
        "strengths": plan.strengths,
        "weaknesses": plan.weaknesses,
        "opportunities": plan.opportunities,
        "threats": plan.threats,
        "grant_end_date": plan.grant_end_date.isoformat() if plan.grant_end_date else None,
        "transition_plan": plan.transition_plan,
        "institutionalization_strategy": plan.institutionalization_strategy,
        "funding_strategies": [
            {
                "id": str(s.id),
                "funding_source": s.funding_source.value,
                "strategy_name": s.strategy_name,
                "current_amount": s.current_amount,
                "year_1_target": s.year_1_target,
                "year_2_target": s.year_2_target,
                "year_3_target": s.year_3_target,
                "status": s.status,
            }
            for s in strategies_result.scalars()
        ],
        "capacity_elements": [
            {
                "id": str(c.id),
                "element_type": c.element_type,
                "element_name": c.element_name,
                "current_status": c.current_status,
                "target_status": c.target_status,
                "progress_percentage": c.progress_percentage,
            }
            for c in capacity_result.scalars()
        ],
    }


@router.post("/strategies")
async def add_funding_strategy(
    data: FundingStrategyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a funding strategy."""
    strategy = FundingStrategy(**data.dict())
    db.add(strategy)
    await db.commit()
    return {"id": str(strategy.id)}


@router.post("/capacity-elements")
async def add_capacity_element(
    data: CapacityElementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a capacity building element."""
    element = CapacityElement(**data.dict())
    db.add(element)
    await db.commit()
    return {"id": str(element.id)}


@router.get("/types")
async def get_sustainability_types():
    """Get available types."""
    return {
        "funding_sources": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in FundingSource
        ],
        "capacity_types": [
            {"value": "human", "label": "Human Capacity"},
            {"value": "organizational", "label": "Organizational Capacity"},
            {"value": "financial", "label": "Financial Capacity"},
            {"value": "technical", "label": "Technical Capacity"},
            {"value": "governance", "label": "Governance"},
        ],
    }
