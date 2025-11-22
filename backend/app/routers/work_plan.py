"""Work Plan and Gantt Chart API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.work_plan import (
    WorkPlan, WorkPlanPhase, WorkPlanActivity, WorkPlanSubTask, WorkPlanMilestone,
    TaskStatus
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/work-plans", tags=["Work Plans"])


class WorkPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    project_id: Optional[UUID] = None
    total_budget: Optional[float] = None


class PhaseCreate(BaseModel):
    work_plan_id: UUID
    phase_name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    color: Optional[str] = None


class ActivityCreate(BaseModel):
    phase_id: UUID
    activity_name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    responsible_person: Optional[str] = None
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    deliverables: Optional[List[str]] = None
    predecessors: Optional[List[str]] = None


class MilestoneCreate(BaseModel):
    work_plan_id: UUID
    milestone_name: str
    description: Optional[str] = None
    due_date: datetime
    deliverables: Optional[List[str]] = None
    is_reporting_milestone: bool = False
    report_type: Optional[str] = None


@router.post("/")
async def create_work_plan(
    data: WorkPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a work plan."""
    work_plan = WorkPlan(user_id=current_user.id, **data.dict())
    db.add(work_plan)
    await db.commit()
    await db.refresh(work_plan)
    return {"id": str(work_plan.id), "title": work_plan.title}


@router.get("/")
async def list_work_plans(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List work plans."""
    stmt = select(WorkPlan).where(WorkPlan.user_id == current_user.id)
    if project_id:
        stmt = stmt.where(WorkPlan.project_id == project_id)

    result = await db.execute(stmt.order_by(WorkPlan.created_at.desc()))

    return {
        "work_plans": [
            {
                "id": str(w.id),
                "title": w.title,
                "start_date": w.start_date.isoformat(),
                "end_date": w.end_date.isoformat(),
                "status": w.status,
            }
            for w in result.scalars()
        ]
    }


@router.get("/{work_plan_id}")
async def get_work_plan(
    work_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get work plan with phases, activities, and milestones."""
    work_plan = await db.get(WorkPlan, work_plan_id)
    if not work_plan or work_plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Work plan not found")

    phases_result = await db.execute(
        select(WorkPlanPhase)
        .where(WorkPlanPhase.work_plan_id == work_plan_id)
        .order_by(WorkPlanPhase.order_index)
    )

    milestones_result = await db.execute(
        select(WorkPlanMilestone)
        .where(WorkPlanMilestone.work_plan_id == work_plan_id)
        .order_by(WorkPlanMilestone.due_date)
    )

    phases = []
    for phase in phases_result.scalars():
        activities_result = await db.execute(
            select(WorkPlanActivity)
            .where(WorkPlanActivity.phase_id == phase.id)
            .order_by(WorkPlanActivity.order_index)
        )

        activities = []
        for act in activities_result.scalars():
            subtasks_result = await db.execute(
                select(WorkPlanSubTask)
                .where(WorkPlanSubTask.activity_id == act.id)
                .order_by(WorkPlanSubTask.order_index)
            )

            activities.append({
                "id": str(act.id),
                "activity_name": act.activity_name,
                "description": act.description,
                "start_date": act.start_date.isoformat(),
                "end_date": act.end_date.isoformat(),
                "duration_days": (act.end_date - act.start_date).days,
                "responsible_person": act.responsible_person,
                "status": act.status.value,
                "progress_percentage": act.progress_percentage,
                "is_critical_path": act.is_critical_path,
                "predecessors": act.predecessors,
                "deliverables": act.deliverables,
                "sub_tasks": [
                    {
                        "id": str(st.id),
                        "task_name": st.task_name,
                        "is_completed": st.is_completed,
                        "assigned_to": st.assigned_to,
                    }
                    for st in subtasks_result.scalars()
                ],
            })

        phases.append({
            "id": str(phase.id),
            "phase_name": phase.phase_name,
            "description": phase.description,
            "start_date": phase.start_date.isoformat(),
            "end_date": phase.end_date.isoformat(),
            "color": phase.color,
            "activities": activities,
        })

    return {
        "id": str(work_plan.id),
        "title": work_plan.title,
        "description": work_plan.description,
        "start_date": work_plan.start_date.isoformat(),
        "end_date": work_plan.end_date.isoformat(),
        "total_budget": work_plan.total_budget,
        "status": work_plan.status,
        "phases": phases,
        "milestones": [
            {
                "id": str(m.id),
                "milestone_name": m.milestone_name,
                "due_date": m.due_date.isoformat(),
                "deliverables": m.deliverables,
                "is_reporting_milestone": m.is_reporting_milestone,
                "status": m.status,
            }
            for m in milestones_result.scalars()
        ],
    }


@router.get("/{work_plan_id}/gantt")
async def get_gantt_data(
    work_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get data formatted for Gantt chart visualization."""
    work_plan = await db.get(WorkPlan, work_plan_id)
    if not work_plan or work_plan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Work plan not found")

    phases_result = await db.execute(
        select(WorkPlanPhase).where(WorkPlanPhase.work_plan_id == work_plan_id)
    )

    tasks = []
    for phase in phases_result.scalars():
        tasks.append({
            "id": str(phase.id),
            "name": phase.phase_name,
            "start": phase.start_date.isoformat(),
            "end": phase.end_date.isoformat(),
            "type": "phase",
            "color": phase.color or "#3b82f6",
        })

        activities_result = await db.execute(
            select(WorkPlanActivity).where(WorkPlanActivity.phase_id == phase.id)
        )

        for act in activities_result.scalars():
            tasks.append({
                "id": str(act.id),
                "name": act.activity_name,
                "start": act.start_date.isoformat(),
                "end": act.end_date.isoformat(),
                "type": "activity",
                "parent": str(phase.id),
                "progress": act.progress_percentage,
                "dependencies": act.predecessors or [],
                "assignee": act.responsible_person,
            })

    milestones_result = await db.execute(
        select(WorkPlanMilestone).where(WorkPlanMilestone.work_plan_id == work_plan_id)
    )

    milestones = [
        {
            "id": str(m.id),
            "name": m.milestone_name,
            "date": m.due_date.isoformat(),
            "type": "milestone",
        }
        for m in milestones_result.scalars()
    ]

    return {
        "project_start": work_plan.start_date.isoformat(),
        "project_end": work_plan.end_date.isoformat(),
        "tasks": tasks,
        "milestones": milestones,
    }


@router.post("/phases")
async def create_phase(
    data: PhaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a work plan phase."""
    phase = WorkPlanPhase(**data.dict())
    db.add(phase)
    await db.commit()
    return {"id": str(phase.id)}


@router.post("/activities")
async def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an activity."""
    activity = WorkPlanActivity(
        duration_days=(data.end_date - data.start_date).days,
        **data.dict()
    )
    db.add(activity)
    await db.commit()
    return {"id": str(activity.id)}


@router.patch("/activities/{activity_id}/progress")
async def update_activity_progress(
    activity_id: UUID,
    progress_percentage: int,
    status: Optional[TaskStatus] = None,
    progress_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update activity progress."""
    activity = await db.get(WorkPlanActivity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity.progress_percentage = progress_percentage
    if status:
        activity.status = status
    if progress_notes:
        activity.progress_notes = progress_notes
    if progress_percentage == 100:
        activity.status = TaskStatus.COMPLETED
        activity.actual_end_date = datetime.utcnow()

    await db.commit()
    return {"message": "Progress updated"}


@router.post("/milestones")
async def create_milestone(
    data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a milestone."""
    milestone = WorkPlanMilestone(**data.dict())
    db.add(milestone)
    await db.commit()
    return {"id": str(milestone.id)}


@router.get("/statuses")
async def get_task_statuses():
    """Get available task statuses."""
    return {
        "statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in TaskStatus
        ],
    }
