"""Application Tracking Pipeline API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.application_tracking import (
    GrantApplication, ApplicationTask, ApplicationDocument, StageHistory,
    ApplicationStage, ApplicationPriority
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/applications", tags=["Application Tracking"])


class ApplicationCreate(BaseModel):
    application_name: str
    funder_name: str
    program_name: Optional[str] = None
    amount_requested: Optional[float] = None
    application_deadline: Optional[datetime] = None
    project_id: Optional[UUID] = None
    priority: ApplicationPriority = ApplicationPriority.MEDIUM
    lead_writer: Optional[str] = None
    match_required: bool = False
    match_amount: Optional[float] = None


class TaskCreate(BaseModel):
    application_id: UUID
    task_name: str
    description: Optional[str] = None
    task_type: str = "general"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"


class DocumentCreate(BaseModel):
    application_id: UUID
    document_name: str
    document_type: str
    is_required: bool = True
    due_date: Optional[datetime] = None


class StageUpdate(BaseModel):
    stage: ApplicationStage
    notes: Optional[str] = None


@router.post("/")
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new grant application."""
    application = GrantApplication(
        user_id=current_user.id,
        opportunity_identified_date=datetime.utcnow(),
        **data.dict()
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    # Create initial stage history
    history = StageHistory(
        application_id=application.id,
        to_stage=application.stage.value,
        changed_by=current_user.email,
        notes="Application created"
    )
    db.add(history)
    await db.commit()

    return {"id": str(application.id), "name": application.application_name}


@router.get("/")
async def list_applications(
    stage: Optional[ApplicationStage] = None,
    priority: Optional[ApplicationPriority] = None,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List grant applications."""
    stmt = select(GrantApplication).where(GrantApplication.user_id == current_user.id)

    if stage:
        stmt = stmt.where(GrantApplication.stage == stage)
    if priority:
        stmt = stmt.where(GrantApplication.priority == priority)
    if project_id:
        stmt = stmt.where(GrantApplication.project_id == project_id)

    result = await db.execute(stmt.order_by(GrantApplication.application_deadline))

    return {
        "applications": [
            {
                "id": str(a.id),
                "application_name": a.application_name,
                "funder_name": a.funder_name,
                "amount_requested": a.amount_requested,
                "stage": a.stage.value,
                "priority": a.priority.value,
                "probability": a.probability,
                "application_deadline": a.application_deadline.isoformat() if a.application_deadline else None,
                "lead_writer": a.lead_writer,
            }
            for a in result.scalars()
        ]
    }


@router.get("/pipeline")
async def get_pipeline_view(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline view grouped by stage."""
    result = await db.execute(
        select(GrantApplication).where(GrantApplication.user_id == current_user.id)
    )

    pipeline = {stage.value: [] for stage in ApplicationStage}
    total_pipeline_value = 0
    weighted_pipeline_value = 0

    for app in result.scalars():
        pipeline[app.stage.value].append({
            "id": str(app.id),
            "application_name": app.application_name,
            "funder_name": app.funder_name,
            "amount_requested": app.amount_requested,
            "priority": app.priority.value,
            "probability": app.probability,
            "deadline": app.application_deadline.isoformat() if app.application_deadline else None,
        })
        if app.amount_requested:
            total_pipeline_value += app.amount_requested
            if app.probability:
                weighted_pipeline_value += app.amount_requested * (app.probability / 100)

    return {
        "pipeline": pipeline,
        "summary": {
            "total_applications": sum(len(apps) for apps in pipeline.values()),
            "total_pipeline_value": total_pipeline_value,
            "weighted_pipeline_value": weighted_pipeline_value,
        }
    }


@router.get("/{application_id}")
async def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application details."""
    app = await db.get(GrantApplication, application_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    tasks_result = await db.execute(
        select(ApplicationTask).where(ApplicationTask.application_id == application_id)
    )
    docs_result = await db.execute(
        select(ApplicationDocument).where(ApplicationDocument.application_id == application_id)
    )
    history_result = await db.execute(
        select(StageHistory)
        .where(StageHistory.application_id == application_id)
        .order_by(StageHistory.change_date.desc())
    )

    return {
        "id": str(app.id),
        "application_name": app.application_name,
        "funder_name": app.funder_name,
        "program_name": app.program_name,
        "amount_requested": app.amount_requested,
        "amount_awarded": app.amount_awarded,
        "stage": app.stage.value,
        "priority": app.priority.value,
        "probability": app.probability,
        "match_required": app.match_required,
        "match_amount": app.match_amount,
        "match_secured": app.match_secured,
        "application_deadline": app.application_deadline.isoformat() if app.application_deadline else None,
        "submitted_date": app.submitted_date.isoformat() if app.submitted_date else None,
        "decision_date": app.decision_date.isoformat() if app.decision_date else None,
        "lead_writer": app.lead_writer,
        "team_members": app.team_members,
        "submission_method": app.submission_method,
        "confirmation_number": app.confirmation_number,
        "decision_notes": app.decision_notes,
        "feedback_received": app.feedback_received,
        "tasks": [
            {
                "id": str(t.id),
                "task_name": t.task_name,
                "task_type": t.task_type,
                "assigned_to": t.assigned_to,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "status": t.status,
                "priority": t.priority,
            }
            for t in tasks_result.scalars()
        ],
        "documents": [
            {
                "id": str(d.id),
                "document_name": d.document_name,
                "document_type": d.document_type,
                "is_required": d.is_required,
                "status": d.status,
                "version": d.version,
            }
            for d in docs_result.scalars()
        ],
        "stage_history": [
            {
                "from_stage": h.from_stage,
                "to_stage": h.to_stage,
                "changed_by": h.changed_by,
                "change_date": h.change_date.isoformat(),
                "notes": h.notes,
            }
            for h in history_result.scalars()
        ],
    }


@router.patch("/{application_id}/stage")
async def update_application_stage(
    application_id: UUID,
    data: StageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update application stage."""
    app = await db.get(GrantApplication, application_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    old_stage = app.stage.value
    app.stage = data.stage

    # Record stage change
    history = StageHistory(
        application_id=application_id,
        from_stage=old_stage,
        to_stage=data.stage.value,
        changed_by=current_user.email,
        notes=data.notes
    )
    db.add(history)

    # Update relevant dates
    if data.stage == ApplicationStage.SUBMITTED:
        app.submitted_date = datetime.utcnow()
    elif data.stage in [ApplicationStage.AWARDED, ApplicationStage.DECLINED]:
        app.decision_date = datetime.utcnow()

    await db.commit()
    return {"message": "Stage updated"}


@router.post("/tasks")
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an application task."""
    task = ApplicationTask(**data.dict())
    db.add(task)
    await db.commit()
    return {"id": str(task.id)}


@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: UUID,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task status."""
    task = await db.get(ApplicationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = status
    if status == "completed":
        task.completed_date = datetime.utcnow()
    await db.commit()
    return {"message": "Task updated"}


@router.post("/documents")
async def create_document(
    data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an application document tracker."""
    doc = ApplicationDocument(**data.dict())
    db.add(doc)
    await db.commit()
    return {"id": str(doc.id)}


@router.get("/stages")
async def get_stages():
    """Get available stages and priorities."""
    return {
        "stages": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in ApplicationStage
        ],
        "priorities": [
            {"value": p.value, "label": p.value.title()}
            for p in ApplicationPriority
        ],
        "task_types": [
            {"value": "writing", "label": "Writing"},
            {"value": "review", "label": "Review"},
            {"value": "document", "label": "Document Collection"},
            {"value": "submission", "label": "Submission"},
            {"value": "research", "label": "Research"},
            {"value": "meeting", "label": "Meeting"},
            {"value": "general", "label": "General"},
        ],
        "document_types": [
            {"value": "proposal", "label": "Proposal Narrative"},
            {"value": "budget", "label": "Budget"},
            {"value": "budget_narrative", "label": "Budget Narrative"},
            {"value": "logic_model", "label": "Logic Model"},
            {"value": "timeline", "label": "Timeline"},
            {"value": "org_chart", "label": "Org Chart"},
            {"value": "501c3", "label": "501(c)(3) Letter"},
            {"value": "audit", "label": "Audit Report"},
            {"value": "board_list", "label": "Board List"},
            {"value": "support_letter", "label": "Letter of Support"},
            {"value": "mou", "label": "MOU"},
            {"value": "resume", "label": "Staff Resume"},
            {"value": "other", "label": "Other"},
        ],
    }
