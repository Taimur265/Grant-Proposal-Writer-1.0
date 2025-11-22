"""Evaluation Plan API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.evaluation import (
    EvaluationPlan, EvalDataCollection, EvaluationIndicator, DataCollectionSchedule,
    EvaluationType, EvaluationDesign
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/evaluation", tags=["Evaluation & M&E"])


# Schemas
class EvaluationPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    evaluation_type: EvaluationType
    evaluation_design: EvaluationDesign
    evaluation_purpose: str
    key_questions: Optional[List[str]] = None
    project_id: Optional[UUID] = None
    evaluator_type: str = "internal"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class DataCollectionCreate(BaseModel):
    evaluation_plan_id: UUID
    method_name: str
    method_type: str
    description: Optional[str] = None
    target_population: Optional[str] = None
    sampling_strategy: Optional[str] = None
    sample_size: Optional[int] = None
    collection_frequency: Optional[str] = None
    responsible_person: Optional[str] = None
    analysis_approach: Optional[str] = None


class EvalIndicatorCreate(BaseModel):
    evaluation_plan_id: UUID
    indicator_name: str
    indicator_type: str
    definition: str
    data_source: str
    collection_method: str
    frequency: str
    target: str
    baseline: Optional[str] = None
    disaggregation: Optional[List[str]] = None


# Evaluation Plan CRUD
@router.post("/plans")
async def create_evaluation_plan(
    data: EvaluationPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an evaluation plan."""
    plan = EvaluationPlan(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"id": str(plan.id), "title": plan.title}


@router.get("/plans")
async def list_evaluation_plans(
    project_id: Optional[UUID] = None,
    evaluation_type: Optional[EvaluationType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List evaluation plans."""
    stmt = select(EvaluationPlan).where(EvaluationPlan.user_id == current_user.id)

    if project_id:
        stmt = stmt.where(EvaluationPlan.project_id == project_id)
    if evaluation_type:
        stmt = stmt.where(EvaluationPlan.evaluation_type == evaluation_type)

    result = await db.execute(stmt.order_by(EvaluationPlan.created_at.desc()))

    return {
        "plans": [
            {
                "id": str(p.id),
                "title": p.title,
                "evaluation_type": p.evaluation_type.value,
                "evaluation_design": p.evaluation_design.value,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in result.scalars()
        ]
    }


@router.get("/plans/{plan_id}")
async def get_evaluation_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get evaluation plan with details."""
    plan = await db.get(EvaluationPlan, plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get data collection methods
    methods_result = await db.execute(
        select(EvalDataCollection).where(EvalDataCollection.evaluation_plan_id == plan_id)
    )

    # Get indicators
    indicators_result = await db.execute(
        select(EvaluationIndicator).where(EvaluationIndicator.evaluation_plan_id == plan_id)
    )

    return {
        "id": str(plan.id),
        "title": plan.title,
        "description": plan.description,
        "evaluation_type": plan.evaluation_type.value,
        "evaluation_design": plan.evaluation_design.value,
        "evaluation_purpose": plan.evaluation_purpose,
        "key_questions": plan.key_questions,
        "primary_users": plan.primary_users,
        "evaluator_type": plan.evaluator_type,
        "evaluator_name": plan.evaluator_name,
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "irb_required": plan.irb_required,
        "irb_status": plan.irb_status,
        "known_limitations": plan.known_limitations,
        "dissemination_plan": plan.dissemination_plan,
        "status": plan.status,
        "data_collection_methods": [
            {
                "id": str(m.id),
                "method_name": m.method_name,
                "method_type": m.method_type,
                "target_population": m.target_population,
                "sample_size": m.sample_size,
                "collection_frequency": m.collection_frequency,
            }
            for m in methods_result.scalars()
        ],
        "indicators": [
            {
                "id": str(i.id),
                "indicator_name": i.indicator_name,
                "indicator_type": i.indicator_type,
                "definition": i.definition,
                "data_source": i.data_source,
                "baseline": i.baseline,
                "target": i.target,
                "frequency": i.frequency,
            }
            for i in indicators_result.scalars()
        ],
    }


# Data Collection Methods
@router.post("/data-collection")
async def add_data_collection_method(
    data: DataCollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a data collection method."""
    method = EvalDataCollection(**data.dict())
    db.add(method)
    await db.commit()
    return {"id": str(method.id)}


# Evaluation Indicators
@router.post("/indicators")
async def add_evaluation_indicator(
    data: EvalIndicatorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an evaluation indicator."""
    indicator = EvaluationIndicator(**data.dict())
    db.add(indicator)
    await db.commit()
    return {"id": str(indicator.id)}


@router.get("/types")
async def get_evaluation_types():
    """Get available evaluation types and designs."""
    return {
        "evaluation_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in EvaluationType
        ],
        "evaluation_designs": [
            {"value": d.value, "label": d.value.replace("_", " ").title()}
            for d in EvaluationDesign
        ],
        "method_types": [
            {"value": "quantitative", "label": "Quantitative"},
            {"value": "qualitative", "label": "Qualitative"},
            {"value": "mixed", "label": "Mixed Methods"},
        ],
        "indicator_types": [
            {"value": "process", "label": "Process Indicator"},
            {"value": "output", "label": "Output Indicator"},
            {"value": "outcome", "label": "Outcome Indicator"},
            {"value": "impact", "label": "Impact Indicator"},
        ],
        "frequencies": [
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"},
            {"value": "annually", "label": "Annually"},
            {"value": "baseline_endline", "label": "Baseline/Endline"},
        ],
    }


# M&E Framework Template
@router.get("/framework-template")
async def get_me_framework_template():
    """Get a standard M&E framework template."""
    return {
        "framework": {
            "sections": [
                {
                    "name": "Theory of Change",
                    "description": "Logic model linking inputs to impacts",
                    "components": ["inputs", "activities", "outputs", "outcomes", "impacts"]
                },
                {
                    "name": "Indicators",
                    "description": "Measurable indicators for each level",
                    "levels": ["output", "outcome", "impact"]
                },
                {
                    "name": "Data Collection",
                    "description": "Methods and schedule for data collection",
                    "elements": ["methods", "tools", "frequency", "responsible_parties"]
                },
                {
                    "name": "Analysis Plan",
                    "description": "How data will be analyzed",
                    "elements": ["quantitative_analysis", "qualitative_analysis", "triangulation"]
                },
                {
                    "name": "Reporting",
                    "description": "Reporting schedule and formats",
                    "elements": ["reports", "dashboards", "stakeholder_communication"]
                },
                {
                    "name": "Learning & Adaptation",
                    "description": "How findings will inform program improvement",
                    "elements": ["feedback_loops", "adaptive_management", "knowledge_sharing"]
                }
            ]
        }
    }
