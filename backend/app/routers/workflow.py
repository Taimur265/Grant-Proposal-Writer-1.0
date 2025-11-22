"""Workflow and approval API routes."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.user import User
from app.models.workflow import (
    WorkflowTemplate, Workflow, WorkflowApproval, WorkflowHistory,
    WorkflowStatus, ApprovalType
)
from app.models.collaboration import Notification
from app.routers.auth import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# Schemas
class WorkflowTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    approval_type: str = "proposal_review"
    steps: List[dict] = []
    is_sequential: bool = True
    require_all_approvers: bool = True


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_type: str
    target_id: UUID
    project_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    approver_ids: List[UUID]
    due_date: Optional[datetime] = None


class ApprovalDecision(BaseModel):
    decision: str  # 'approve', 'reject', 'request_revision'
    comments: Optional[str] = None
    requested_changes: Optional[str] = None


# Template endpoints
@router.post("/templates")
async def create_template(
    template_data: WorkflowTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a workflow template."""
    template = WorkflowTemplate(
        name=template_data.name,
        description=template_data.description,
        approval_type=ApprovalType(template_data.approval_type),
        steps=template_data.steps,
        is_sequential=template_data.is_sequential,
        require_all_approvers=template_data.require_all_approvers,
        created_by_id=current_user.id,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {"id": str(template.id), "name": template.name}


@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workflow templates."""
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.is_active == True)
    )

    templates = []
    for template in result.scalars():
        templates.append({
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "approval_type": template.approval_type.value,
            "steps_count": len(template.steps),
            "is_default": template.is_default,
        })

    return {"templates": templates}


# Workflow endpoints
@router.post("/")
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow."""
    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        target_type=workflow_data.target_type,
        target_id=workflow_data.target_id,
        project_id=workflow_data.project_id,
        template_id=workflow_data.template_id,
        initiated_by_id=current_user.id,
        due_date=workflow_data.due_date,
        total_steps=len(workflow_data.approver_ids),
    )

    db.add(workflow)
    await db.flush()

    # Create approval entries for each approver
    for i, approver_id in enumerate(workflow_data.approver_ids, 1):
        approval = WorkflowApproval(
            workflow_id=workflow.id,
            step_number=i,
            approver_id=approver_id,
            due_date=workflow_data.due_date,
        )
        db.add(approval)

        # Create notification for approver
        notification = Notification(
            user_id=approver_id,
            title="Review Requested",
            message=f"You have been assigned to review: {workflow_data.name}",
            notification_type="workflow",
            link_type="workflow",
            link_id=workflow.id,
        )
        db.add(notification)

    # Log history
    history = WorkflowHistory(
        workflow_id=workflow.id,
        action="created",
        action_by_id=current_user.id,
        new_status=WorkflowStatus.PENDING.value,
    )
    db.add(history)

    await db.commit()
    await db.refresh(workflow)

    return {"id": str(workflow.id), "name": workflow.name}


@router.get("/")
async def list_workflows(
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workflows initiated by or assigned to user."""
    # Workflows initiated by user
    initiated_stmt = select(Workflow).where(Workflow.initiated_by_id == current_user.id)

    # Workflows assigned to user
    assigned_stmt = (
        select(Workflow)
        .join(WorkflowApproval)
        .where(WorkflowApproval.approver_id == current_user.id)
    )

    if status:
        initiated_stmt = initiated_stmt.where(Workflow.status == WorkflowStatus(status))
        assigned_stmt = assigned_stmt.where(Workflow.status == WorkflowStatus(status))

    if target_type:
        initiated_stmt = initiated_stmt.where(Workflow.target_type == target_type)
        assigned_stmt = assigned_stmt.where(Workflow.target_type == target_type)

    initiated_result = await db.execute(initiated_stmt)
    assigned_result = await db.execute(assigned_stmt)

    # Combine and deduplicate
    workflow_ids = set()
    workflows = []

    for workflow in list(initiated_result.scalars()) + list(assigned_result.scalars()):
        if workflow.id not in workflow_ids:
            workflow_ids.add(workflow.id)
            workflows.append({
                "id": str(workflow.id),
                "name": workflow.name,
                "description": workflow.description,
                "target_type": workflow.target_type,
                "target_id": str(workflow.target_id),
                "status": workflow.status.value,
                "current_step": workflow.current_step,
                "total_steps": workflow.total_steps,
                "due_date": workflow.due_date.isoformat() if workflow.due_date else None,
                "created_at": workflow.created_at.isoformat(),
                "is_initiator": workflow.initiated_by_id == current_user.id,
            })

    return {"workflows": workflows}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workflow details."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get approvals
    approvals_result = await db.execute(
        select(WorkflowApproval)
        .where(WorkflowApproval.workflow_id == workflow_id)
        .order_by(WorkflowApproval.step_number)
    )

    approvals = []
    for approval in approvals_result.scalars():
        approvals.append({
            "id": str(approval.id),
            "step_number": approval.step_number,
            "step_name": approval.step_name,
            "approver_id": str(approval.approver_id),
            "status": approval.status.value,
            "decision": approval.decision,
            "comments": approval.comments,
            "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
        })

    # Get history
    history_result = await db.execute(
        select(WorkflowHistory)
        .where(WorkflowHistory.workflow_id == workflow_id)
        .order_by(WorkflowHistory.created_at.desc())
    )

    history = []
    for entry in history_result.scalars():
        history.append({
            "action": entry.action,
            "action_by_id": str(entry.action_by_id),
            "previous_status": entry.previous_status,
            "new_status": entry.new_status,
            "created_at": entry.created_at.isoformat(),
        })

    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "target_type": workflow.target_type,
        "target_id": str(workflow.target_id),
        "status": workflow.status.value,
        "current_step": workflow.current_step,
        "total_steps": workflow.total_steps,
        "due_date": workflow.due_date.isoformat() if workflow.due_date else None,
        "initiated_by_id": str(workflow.initiated_by_id),
        "created_at": workflow.created_at.isoformat(),
        "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
        "approvals": approvals,
        "history": history,
    }


@router.post("/{workflow_id}/approve")
async def submit_approval(
    workflow_id: UUID,
    decision_data: ApprovalDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit approval decision."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Find pending approval for current user
    approval_result = await db.execute(
        select(WorkflowApproval).where(
            and_(
                WorkflowApproval.workflow_id == workflow_id,
                WorkflowApproval.approver_id == current_user.id,
                WorkflowApproval.status == WorkflowStatus.PENDING,
            )
        )
    )
    approval = approval_result.scalar_one_or_none()

    if not approval:
        raise HTTPException(status_code=400, detail="No pending approval found for you")

    previous_status = workflow.status.value

    # Update approval
    approval.decision = decision_data.decision
    approval.comments = decision_data.comments
    approval.requested_changes = decision_data.requested_changes
    approval.reviewed_at = datetime.utcnow()

    if decision_data.decision == "approve":
        approval.status = WorkflowStatus.APPROVED
        workflow.current_step += 1

        # Check if all approvals complete
        if workflow.current_step >= workflow.total_steps:
            workflow.status = WorkflowStatus.APPROVED
            workflow.completed_at = datetime.utcnow()
        else:
            workflow.status = WorkflowStatus.IN_REVIEW

    elif decision_data.decision == "reject":
        approval.status = WorkflowStatus.REJECTED
        workflow.status = WorkflowStatus.REJECTED
        workflow.completed_at = datetime.utcnow()

    elif decision_data.decision == "request_revision":
        approval.status = WorkflowStatus.REVISION_REQUESTED
        workflow.status = WorkflowStatus.REVISION_REQUESTED

    # Log history
    history = WorkflowHistory(
        workflow_id=workflow.id,
        action=f"approval_{decision_data.decision}",
        action_by_id=current_user.id,
        action_details={"comments": decision_data.comments},
        previous_status=previous_status,
        new_status=workflow.status.value,
    )
    db.add(history)

    # Notify initiator
    notification = Notification(
        user_id=workflow.initiated_by_id,
        title=f"Workflow {decision_data.decision.replace('_', ' ').title()}",
        message=f"Your workflow '{workflow.name}' has been {decision_data.decision.replace('_', ' ')}",
        notification_type="workflow",
        link_type="workflow",
        link_id=workflow.id,
    )
    db.add(notification)

    await db.commit()

    return {
        "message": f"Approval {decision_data.decision} submitted",
        "workflow_status": workflow.status.value,
    }


@router.get("/pending")
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending approvals for current user."""
    result = await db.execute(
        select(WorkflowApproval)
        .join(Workflow)
        .where(
            and_(
                WorkflowApproval.approver_id == current_user.id,
                WorkflowApproval.status == WorkflowStatus.PENDING,
            )
        )
        .order_by(WorkflowApproval.due_date.asc().nullslast())
    )

    pending = []
    for approval in result.scalars():
        workflow = await db.get(Workflow, approval.workflow_id)
        pending.append({
            "approval_id": str(approval.id),
            "workflow_id": str(approval.workflow_id),
            "workflow_name": workflow.name if workflow else None,
            "target_type": workflow.target_type if workflow else None,
            "step_number": approval.step_number,
            "due_date": approval.due_date.isoformat() if approval.due_date else None,
            "assigned_at": approval.assigned_at.isoformat(),
        })

    return {"pending_approvals": pending}
