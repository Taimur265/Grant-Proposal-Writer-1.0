"""Timeline and milestone API routes."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.timeline import Milestone, MilestoneStatus, Task, TaskPriority, ProjectPhase
from app.routers.auth import get_current_user

router = APIRouter(prefix="/timeline", tags=["Timeline"])


# Schemas
class MilestoneCreate(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    depends_on_id: Optional[UUID] = None
    deliverables: Optional[str] = None
    order_index: int = 0


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    progress_percentage: Optional[float] = None
    deliverables: Optional[str] = None


class TaskCreate(BaseModel):
    milestone_id: UUID
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    assigned_to_id: Optional[UUID] = None
    order_index: int = 0


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    actual_hours: Optional[float] = None


class PhaseCreate(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    order_index: int = 0


# Milestone endpoints
@router.post("/milestones")
async def create_milestone(
    milestone_data: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new milestone."""
    milestone = Milestone(
        project_id=milestone_data.project_id,
        title=milestone_data.title,
        description=milestone_data.description,
        planned_start=milestone_data.planned_start,
        planned_end=milestone_data.planned_end,
        depends_on_id=milestone_data.depends_on_id,
        deliverables=milestone_data.deliverables,
        order_index=milestone_data.order_index,
    )

    db.add(milestone)
    await db.commit()
    await db.refresh(milestone)

    return {
        "id": str(milestone.id),
        "title": milestone.title,
        "status": milestone.status.value,
        "created_at": milestone.created_at.isoformat(),
    }


@router.get("/milestones/project/{project_id}")
async def get_project_milestones(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all milestones for a project."""
    result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.order_index)
    )

    milestones = []
    for milestone in result.scalars():
        # Get task count
        task_result = await db.execute(
            select(Task).where(Task.milestone_id == milestone.id)
        )
        tasks = list(task_result.scalars())
        completed_tasks = len([t for t in tasks if t.is_completed])

        milestones.append({
            "id": str(milestone.id),
            "title": milestone.title,
            "description": milestone.description,
            "status": milestone.status.value,
            "planned_start": milestone.planned_start.isoformat() if milestone.planned_start else None,
            "planned_end": milestone.planned_end.isoformat() if milestone.planned_end else None,
            "actual_start": milestone.actual_start.isoformat() if milestone.actual_start else None,
            "actual_end": milestone.actual_end.isoformat() if milestone.actual_end else None,
            "progress_percentage": milestone.progress_percentage,
            "deliverables": milestone.deliverables,
            "task_count": len(tasks),
            "completed_tasks": completed_tasks,
            "order_index": milestone.order_index,
        })

    return {"milestones": milestones}


@router.get("/milestones/{milestone_id}")
async def get_milestone(
    milestone_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific milestone with tasks."""
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # Get tasks
    task_result = await db.execute(
        select(Task)
        .where(Task.milestone_id == milestone_id)
        .order_by(Task.order_index)
    )

    tasks = []
    for task in task_result.scalars():
        tasks.append({
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "is_completed": task.is_completed,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "assigned_to_id": str(task.assigned_to_id) if task.assigned_to_id else None,
        })

    return {
        "id": str(milestone.id),
        "title": milestone.title,
        "description": milestone.description,
        "status": milestone.status.value,
        "planned_start": milestone.planned_start.isoformat() if milestone.planned_start else None,
        "planned_end": milestone.planned_end.isoformat() if milestone.planned_end else None,
        "actual_start": milestone.actual_start.isoformat() if milestone.actual_start else None,
        "actual_end": milestone.actual_end.isoformat() if milestone.actual_end else None,
        "progress_percentage": milestone.progress_percentage,
        "deliverables": milestone.deliverables,
        "tasks": tasks,
    }


@router.patch("/milestones/{milestone_id}")
async def update_milestone(
    milestone_id: UUID,
    update_data: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a milestone."""
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    update_dict = update_data.dict(exclude_unset=True)

    if "status" in update_dict:
        update_dict["status"] = MilestoneStatus(update_dict["status"])

    for key, value in update_dict.items():
        setattr(milestone, key, value)

    await db.commit()
    await db.refresh(milestone)

    return {"message": "Milestone updated", "id": str(milestone.id)}


@router.delete("/milestones/{milestone_id}")
async def delete_milestone(
    milestone_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a milestone."""
    milestone = await db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    await db.delete(milestone)
    await db.commit()

    return {"message": "Milestone deleted"}


# Task endpoints
@router.post("/tasks")
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    task = Task(
        milestone_id=task_data.milestone_id,
        title=task_data.title,
        description=task_data.description,
        priority=TaskPriority(task_data.priority),
        due_date=task_data.due_date,
        estimated_hours=task_data.estimated_hours,
        assigned_to_id=task_data.assigned_to_id,
        order_index=task_data.order_index,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return {
        "id": str(task.id),
        "title": task.title,
        "priority": task.priority.value,
        "created_at": task.created_at.isoformat(),
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    update_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_dict = update_data.dict(exclude_unset=True)

    if "priority" in update_dict:
        update_dict["priority"] = TaskPriority(update_dict["priority"])

    if "is_completed" in update_dict and update_dict["is_completed"]:
        update_dict["completed_at"] = datetime.utcnow()

    for key, value in update_dict.items():
        setattr(task, key, value)

    # Update milestone progress
    milestone = await db.get(Milestone, task.milestone_id)
    if milestone:
        task_result = await db.execute(
            select(Task).where(Task.milestone_id == milestone.id)
        )
        tasks = list(task_result.scalars())
        if tasks:
            completed = len([t for t in tasks if t.is_completed])
            milestone.progress_percentage = (completed / len(tasks)) * 100

    await db.commit()
    await db.refresh(task)

    return {"message": "Task updated", "id": str(task.id)}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()

    return {"message": "Task deleted"}


# Phase endpoints
@router.post("/phases")
async def create_phase(
    phase_data: PhaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project phase."""
    phase = ProjectPhase(
        project_id=phase_data.project_id,
        name=phase_data.name,
        description=phase_data.description,
        color=phase_data.color,
        start_date=phase_data.start_date,
        end_date=phase_data.end_date,
        order_index=phase_data.order_index,
    )

    db.add(phase)
    await db.commit()
    await db.refresh(phase)

    return {
        "id": str(phase.id),
        "name": phase.name,
        "color": phase.color,
    }


@router.get("/phases/project/{project_id}")
async def get_project_phases(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all phases for a project."""
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.project_id == project_id)
        .order_by(ProjectPhase.order_index)
    )

    phases = []
    for phase in result.scalars():
        phases.append({
            "id": str(phase.id),
            "name": phase.name,
            "description": phase.description,
            "color": phase.color,
            "start_date": phase.start_date.isoformat() if phase.start_date else None,
            "end_date": phase.end_date.isoformat() if phase.end_date else None,
            "order_index": phase.order_index,
        })

    return {"phases": phases}


@router.delete("/phases/{phase_id}")
async def delete_phase(
    phase_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project phase."""
    phase = await db.get(ProjectPhase, phase_id)
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    await db.delete(phase)
    await db.commit()

    return {"message": "Phase deleted"}


# Timeline overview
@router.get("/overview/{project_id}")
async def get_timeline_overview(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete timeline overview for a project."""
    # Get phases
    phases_result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.project_id == project_id)
        .order_by(ProjectPhase.order_index)
    )
    phases = list(phases_result.scalars())

    # Get milestones
    milestones_result = await db.execute(
        select(Milestone)
        .where(Milestone.project_id == project_id)
        .order_by(Milestone.order_index)
    )
    milestones = list(milestones_result.scalars())

    # Calculate overall progress
    total_progress = 0
    if milestones:
        total_progress = sum(m.progress_percentage for m in milestones) / len(milestones)

    # Calculate status summary
    status_summary = {
        "not_started": len([m for m in milestones if m.status == MilestoneStatus.NOT_STARTED]),
        "in_progress": len([m for m in milestones if m.status == MilestoneStatus.IN_PROGRESS]),
        "completed": len([m for m in milestones if m.status == MilestoneStatus.COMPLETED]),
        "delayed": len([m for m in milestones if m.status == MilestoneStatus.DELAYED]),
    }

    # Find upcoming deadlines
    upcoming = []
    now = datetime.utcnow()
    for milestone in milestones:
        if milestone.planned_end and milestone.planned_end > now:
            days_remaining = (milestone.planned_end - now).days
            if days_remaining <= 30:
                upcoming.append({
                    "id": str(milestone.id),
                    "title": milestone.title,
                    "deadline": milestone.planned_end.isoformat(),
                    "days_remaining": days_remaining,
                })

    upcoming.sort(key=lambda x: x["days_remaining"])

    return {
        "phases": [{
            "id": str(p.id),
            "name": p.name,
            "color": p.color,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
        } for p in phases],
        "milestones_count": len(milestones),
        "overall_progress": round(total_progress, 1),
        "status_summary": status_summary,
        "upcoming_deadlines": upcoming[:5],
    }
