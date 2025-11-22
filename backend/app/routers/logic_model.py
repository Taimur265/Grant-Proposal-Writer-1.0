"""Logic model and theory of change API routes."""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.logic_model import (
    LogicModel, LogicModelInput, LogicModelActivity,
    LogicModelOutput, LogicModelOutcome, LogicModelImpact
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/logic-models", tags=["Logic Model"])


# Schemas
class LogicModelCreate(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    target_population: Optional[str] = None
    theory_of_change: Optional[str] = None
    assumptions: Optional[List[str]] = None


class InputCreate(BaseModel):
    logic_model_id: UUID
    category: str
    description: str
    quantity: Optional[str] = None
    source: Optional[str] = None
    status: str = "planned"


class ActivityCreate(BaseModel):
    logic_model_id: UUID
    title: str
    description: str
    input_ids: Optional[List[str]] = None
    frequency: Optional[str] = None
    target_participants: Optional[str] = None


class OutputCreate(BaseModel):
    logic_model_id: UUID
    title: str
    description: str
    indicator: str
    target: Optional[str] = None
    activity_ids: Optional[List[str]] = None


class OutcomeCreate(BaseModel):
    logic_model_id: UUID
    title: str
    description: str
    timeframe: str  # short_term, medium_term, long_term
    indicator: str
    target: Optional[str] = None
    data_source: Optional[str] = None
    output_ids: Optional[List[str]] = None


class ImpactCreate(BaseModel):
    logic_model_id: UUID
    title: str
    description: str
    indicator: Optional[str] = None
    evaluation_approach: Optional[str] = None
    outcome_ids: Optional[List[str]] = None


# Logic Model endpoints
@router.post("/")
async def create_logic_model(
    data: LogicModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new logic model."""
    logic_model = LogicModel(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(logic_model)
    await db.commit()
    await db.refresh(logic_model)
    return {"id": str(logic_model.id), "name": logic_model.name}


@router.get("/")
async def list_logic_models(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List logic models."""
    stmt = select(LogicModel).where(
        LogicModel.user_id == current_user.id,
        LogicModel.is_current == True
    )
    if project_id:
        stmt = stmt.where(LogicModel.project_id == project_id)

    result = await db.execute(stmt.order_by(LogicModel.created_at.desc()))

    return {
        "logic_models": [
            {
                "id": str(lm.id),
                "name": lm.name,
                "description": lm.description,
                "version": lm.version,
                "project_id": str(lm.project_id),
                "created_at": lm.created_at.isoformat(),
            }
            for lm in result.scalars()
        ]
    }


@router.get("/{model_id}")
async def get_logic_model(
    model_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete logic model with all components."""
    model = await db.get(LogicModel, model_id)
    if not model or model.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Logic model not found")

    # Get all components
    inputs_result = await db.execute(
        select(LogicModelInput)
        .where(LogicModelInput.logic_model_id == model_id)
        .order_by(LogicModelInput.order_index)
    )
    activities_result = await db.execute(
        select(LogicModelActivity)
        .where(LogicModelActivity.logic_model_id == model_id)
        .order_by(LogicModelActivity.order_index)
    )
    outputs_result = await db.execute(
        select(LogicModelOutput)
        .where(LogicModelOutput.logic_model_id == model_id)
        .order_by(LogicModelOutput.order_index)
    )
    outcomes_result = await db.execute(
        select(LogicModelOutcome)
        .where(LogicModelOutcome.logic_model_id == model_id)
        .order_by(LogicModelOutcome.order_index)
    )
    impacts_result = await db.execute(
        select(LogicModelImpact)
        .where(LogicModelImpact.logic_model_id == model_id)
        .order_by(LogicModelImpact.order_index)
    )

    return {
        "id": str(model.id),
        "name": model.name,
        "description": model.description,
        "version": model.version,
        "problem_statement": model.problem_statement,
        "target_population": model.target_population,
        "root_causes": model.root_causes,
        "theory_of_change": model.theory_of_change,
        "assumptions": model.assumptions,
        "external_factors": model.external_factors,
        "inputs": [
            {
                "id": str(i.id),
                "category": i.category,
                "description": i.description,
                "quantity": i.quantity,
                "source": i.source,
                "status": i.status,
            }
            for i in inputs_result.scalars()
        ],
        "activities": [
            {
                "id": str(a.id),
                "title": a.title,
                "description": a.description,
                "input_ids": a.input_ids,
                "frequency": a.frequency,
                "target_participants": a.target_participants,
            }
            for a in activities_result.scalars()
        ],
        "outputs": [
            {
                "id": str(o.id),
                "title": o.title,
                "description": o.description,
                "indicator": o.indicator,
                "target": o.target,
                "activity_ids": o.activity_ids,
            }
            for o in outputs_result.scalars()
        ],
        "outcomes": [
            {
                "id": str(oc.id),
                "title": oc.title,
                "description": oc.description,
                "timeframe": oc.timeframe,
                "indicator": oc.indicator,
                "target": oc.target,
                "data_source": oc.data_source,
                "output_ids": oc.output_ids,
            }
            for oc in outcomes_result.scalars()
        ],
        "impacts": [
            {
                "id": str(im.id),
                "title": im.title,
                "description": im.description,
                "indicator": im.indicator,
                "evaluation_approach": im.evaluation_approach,
                "outcome_ids": im.outcome_ids,
            }
            for im in impacts_result.scalars()
        ],
    }


@router.patch("/{model_id}")
async def update_logic_model(
    model_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    problem_statement: Optional[str] = None,
    theory_of_change: Optional[str] = None,
    assumptions: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update logic model basic info."""
    model = await db.get(LogicModel, model_id)
    if not model or model.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Logic model not found")

    if name:
        model.name = name
    if description:
        model.description = description
    if problem_statement:
        model.problem_statement = problem_statement
    if theory_of_change:
        model.theory_of_change = theory_of_change
    if assumptions:
        model.assumptions = assumptions

    await db.commit()
    return {"message": "Logic model updated"}


# Input endpoints
@router.post("/inputs")
async def add_input(
    data: InputCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an input to the logic model."""
    input_item = LogicModelInput(**data.dict())
    db.add(input_item)
    await db.commit()
    return {"id": str(input_item.id)}


@router.delete("/inputs/{input_id}")
async def delete_input(
    input_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an input."""
    input_item = await db.get(LogicModelInput, input_id)
    if not input_item:
        raise HTTPException(status_code=404, detail="Input not found")
    await db.delete(input_item)
    await db.commit()
    return {"message": "Input deleted"}


# Activity endpoints
@router.post("/activities")
async def add_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an activity to the logic model."""
    activity = LogicModelActivity(**data.dict())
    db.add(activity)
    await db.commit()
    return {"id": str(activity.id)}


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an activity."""
    activity = await db.get(LogicModelActivity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(activity)
    await db.commit()
    return {"message": "Activity deleted"}


# Output endpoints
@router.post("/outputs")
async def add_output(
    data: OutputCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an output to the logic model."""
    output = LogicModelOutput(**data.dict())
    db.add(output)
    await db.commit()
    return {"id": str(output.id)}


# Outcome endpoints
@router.post("/outcomes")
async def add_outcome(
    data: OutcomeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an outcome to the logic model."""
    outcome = LogicModelOutcome(**data.dict())
    db.add(outcome)
    await db.commit()
    return {"id": str(outcome.id)}


# Impact endpoints
@router.post("/impacts")
async def add_impact(
    data: ImpactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an impact to the logic model."""
    impact = LogicModelImpact(**data.dict())
    db.add(impact)
    await db.commit()
    return {"id": str(impact.id)}


@router.get("/template")
async def get_logic_model_template():
    """Get a template for creating a logic model."""
    return {
        "template": {
            "columns": [
                {
                    "name": "Inputs/Resources",
                    "description": "What resources do you need?",
                    "examples": ["Funding", "Staff", "Equipment", "Partnerships", "Research"],
                    "categories": ["funding", "staff", "equipment", "partnerships", "materials", "technology"],
                },
                {
                    "name": "Activities",
                    "description": "What will you do?",
                    "examples": ["Conduct training", "Provide services", "Develop materials", "Build capacity"],
                },
                {
                    "name": "Outputs",
                    "description": "What will you produce?",
                    "examples": ["# trained", "# served", "Materials created", "Events held"],
                },
                {
                    "name": "Outcomes",
                    "description": "What changes will result?",
                    "timeframes": ["short_term", "medium_term", "long_term"],
                    "examples": {
                        "short_term": "Increased knowledge, Changed attitudes",
                        "medium_term": "Changed behaviors, Improved practices",
                        "long_term": "Sustained change, Systems improvement",
                    },
                },
                {
                    "name": "Impact",
                    "description": "What is the ultimate change?",
                    "examples": ["Improved health outcomes", "Economic development", "Environmental protection"],
                },
            ],
            "guidance": {
                "assumptions": "What conditions must exist for success?",
                "external_factors": "What external factors might affect results?",
                "theory_of_change": "How and why will your activities lead to outcomes?",
            },
        }
    }
