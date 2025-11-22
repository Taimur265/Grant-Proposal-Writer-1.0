"""Workflow and approval models."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class WorkflowStatus(enum.Enum):
    """Status of workflow items."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"


class ApprovalType(enum.Enum):
    """Types of approvals."""
    PROPOSAL_REVIEW = "proposal_review"
    BUDGET_APPROVAL = "budget_approval"
    FINAL_SUBMISSION = "final_submission"
    DOCUMENT_REVIEW = "document_review"


class WorkflowTemplate(Base):
    """Workflow template for approval processes."""

    __tablename__ = "workflow_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    approval_type = Column(Enum(ApprovalType), default=ApprovalType.PROPOSAL_REVIEW)

    # Configuration
    steps = Column(JSON, default=[])  # List of approval steps
    is_sequential = Column(Boolean, default=True)  # Must complete in order
    require_all_approvers = Column(Boolean, default=True)
    auto_approve_after_days = Column(Integer, nullable=True)

    # Ownership
    created_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by = relationship("User", backref="workflow_templates")
    workflows = relationship("Workflow", back_populates="template")


class Workflow(Base):
    """Active workflow instance."""

    __tablename__ = "workflows"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id = Column(PGUUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=True)

    # Context
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Target
    target_type = Column(String(50), nullable=False)  # 'proposal', 'budget', 'document'
    target_id = Column(PGUUID(as_uuid=True), nullable=False)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    # Status
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=1)

    # Initiator
    initiated_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Dates
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="workflows")
    initiated_by = relationship("User", backref="initiated_workflows")
    project = relationship("Project", backref="workflows")
    approvals = relationship("WorkflowApproval", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowApproval(Base):
    """Individual approval within a workflow."""

    __tablename__ = "workflow_approvals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)

    # Step info
    step_number = Column(Integer, default=1)
    step_name = Column(String(255), nullable=True)

    # Approver
    approver_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approver_role = Column(String(100), nullable=True)

    # Status
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    decision = Column(String(50), nullable=True)  # 'approve', 'reject', 'request_revision'

    # Feedback
    comments = Column(Text, nullable=True)
    requested_changes = Column(Text, nullable=True)

    # Dates
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="approvals")
    approver = relationship("User", backref="workflow_approvals")


class WorkflowHistory(Base):
    """History log for workflow actions."""

    __tablename__ = "workflow_history"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(PGUUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)

    # Action info
    action = Column(String(100), nullable=False)
    action_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action_details = Column(JSON, default={})

    # Previous/new state
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", backref="history")
    action_by = relationship("User", backref="workflow_actions")
