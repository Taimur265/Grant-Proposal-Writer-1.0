"""Goals and Objectives API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.goals_objectives import (
    Goal, Objective, ObjectiveActivity, PerformanceIndicator,
    GoalType, ObjectiveStatus
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals & Objectives"])


# Schemas
class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal_type: GoalType = GoalType.PROGRAMMATIC
    target_date: Optional[datetime] = None
    project_id: Optional[UUID] = None
    mission_alignment_notes: Optional[str] = None
    funder_priority_alignment: Optional[str] = None


class ObjectiveCreate(BaseModel):
    goal_id: UUID
    title: str
    specific_statement: str
    description: Optional[str] = None
    measurement_method: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    unit_of_measure: Optional[str] = None
    achievability_rationale: Optional[str] = None
    resources_required: Optional[str] = None
    relevance_to_goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    responsible_person: Optional[str] = None


class ActivityCreate(BaseModel):
    objective_id: UUID
    activity_name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    responsible_person: Optional[str] = None
    resources_needed: Optional[str] = None
    estimated_cost: Optional[float] = None
    deliverables: Optional[List[str]] = None


class IndicatorCreate(BaseModel):
    objective_id: UUID
    indicator_name: str
    indicator_type: str
    definition: Optional[str] = None
    baseline_value: Optional[float] = None
    target_value: float
    unit_of_measure: str
    frequency_of_measurement: Optional[str] = None
    data_source: Optional[str] = None
    data_collection_method: Optional[str] = None


# Goal CRUD
@router.post("/")
async def create_goal(
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new goal."""
    goal = Goal(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return {"id": str(goal.id), "title": goal.title}


@router.get("/")
async def list_goals(
    project_id: Optional[UUID] = None,
    goal_type: Optional[GoalType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all goals."""
    stmt = select(Goal).where(Goal.user_id == current_user.id)

    if project_id:
        stmt = stmt.where(Goal.project_id == project_id)
    if goal_type:
        stmt = stmt.where(Goal.goal_type == goal_type)

    result = await db.execute(stmt.order_by(Goal.order_index, Goal.created_at))

    goals = []
    for g in result.scalars():
        # Get objectives count
        obj_result = await db.execute(
            select(Objective).where(Objective.goal_id == g.id)
        )
        objectives = list(obj_result.scalars())

        goals.append({
            "id": str(g.id),
            "title": g.title,
            "description": g.description,
            "goal_type": g.goal_type.value,
            "target_date": g.target_date.isoformat() if g.target_date else None,
            "progress_percentage": g.progress_percentage,
            "status": g.status,
            "objectives_count": len(objectives),
        })

    return {"goals": goals}


@router.get("/{goal_id}")
async def get_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get goal with all objectives."""
    goal = await db.get(Goal, goal_id)
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Get objectives
    obj_result = await db.execute(
        select(Objective).where(Objective.goal_id == goal_id).order_by(Objective.order_index)
    )

    objectives = []
    for o in obj_result.scalars():
        # Get activities
        act_result = await db.execute(
            select(ObjectiveActivity).where(ObjectiveActivity.objective_id == o.id)
        )
        # Get indicators
        ind_result = await db.execute(
            select(PerformanceIndicator).where(PerformanceIndicator.objective_id == o.id)
        )

        objectives.append({
            "id": str(o.id),
            "title": o.title,
            "specific_statement": o.specific_statement,
            "baseline_value": o.baseline_value,
            "target_value": o.target_value,
            "current_value": o.current_value,
            "unit_of_measure": o.unit_of_measure,
            "start_date": o.start_date.isoformat() if o.start_date else None,
            "end_date": o.end_date.isoformat() if o.end_date else None,
            "status": o.status.value,
            "responsible_person": o.responsible_person,
            "activities": [
                {
                    "id": str(a.id),
                    "activity_name": a.activity_name,
                    "status": a.status,
                    "start_date": a.start_date.isoformat() if a.start_date else None,
                    "end_date": a.end_date.isoformat() if a.end_date else None,
                }
                for a in act_result.scalars()
            ],
            "indicators": [
                {
                    "id": str(i.id),
                    "indicator_name": i.indicator_name,
                    "indicator_type": i.indicator_type,
                    "baseline_value": i.baseline_value,
                    "target_value": i.target_value,
                    "current_value": i.current_value,
                    "unit_of_measure": i.unit_of_measure,
                }
                for i in ind_result.scalars()
            ],
        })

    return {
        "id": str(goal.id),
        "title": goal.title,
        "description": goal.description,
        "goal_type": goal.goal_type.value,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "progress_percentage": goal.progress_percentage,
        "mission_alignment_notes": goal.mission_alignment_notes,
        "funder_priority_alignment": goal.funder_priority_alignment,
        "objectives": objectives,
    }


# Objective CRUD
@router.post("/objectives")
async def create_objective(
    data: ObjectiveCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a SMART objective."""
    objective = Objective(**data.dict())
    db.add(objective)
    await db.commit()
    return {"id": str(objective.id)}


@router.patch("/objectives/{objective_id}/status")
async def update_objective_status(
    objective_id: UUID,
    status: ObjectiveStatus,
    current_value: Optional[float] = None,
    progress_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update objective status and progress."""
    objective = await db.get(Objective, objective_id)
    if not objective:
        raise HTTPException(status_code=404, detail="Objective not found")

    objective.status = status
    if current_value is not None:
        objective.current_value = current_value
    if progress_notes:
        objective.progress_notes = progress_notes

    await db.commit()
    return {"message": "Status updated"}


# Activities
@router.post("/activities")
async def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an activity for an objective."""
    activity = ObjectiveActivity(**data.dict())
    db.add(activity)
    await db.commit()
    return {"id": str(activity.id)}


# Indicators
@router.post("/indicators")
async def create_indicator(
    data: IndicatorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a performance indicator."""
    indicator = PerformanceIndicator(**data.dict())
    db.add(indicator)
    await db.commit()
    return {"id": str(indicator.id)}


@router.patch("/indicators/{indicator_id}/value")
async def update_indicator_value(
    indicator_id: UUID,
    current_value: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update indicator current value."""
    indicator = await db.get(PerformanceIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    indicator.current_value = current_value
    indicator.last_measured_date = datetime.utcnow()
    await db.commit()
    return {"message": "Value updated"}


@router.get("/types")
async def get_goal_types():
    """Get available types and statuses."""
    return {
        "goal_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in GoalType
        ],
        "objective_statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in ObjectiveStatus
        ],
        "indicator_types": [
            {"value": "output", "label": "Output"},
            {"value": "outcome", "label": "Outcome"},
            {"value": "impact", "label": "Impact"},
        ],
    }
