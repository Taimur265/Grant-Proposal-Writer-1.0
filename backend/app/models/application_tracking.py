"""Application Tracking and Pipeline models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class ApplicationStage(str, enum.Enum):
    PROSPECT = "prospect"
    RESEARCHING = "researching"
    LOI_IN_PROGRESS = "loi_in_progress"
    LOI_SUBMITTED = "loi_submitted"
    LOI_APPROVED = "loi_approved"
    PROPOSAL_IN_PROGRESS = "proposal_in_progress"
    INTERNAL_REVIEW = "internal_review"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SITE_VISIT = "site_visit"
    PENDING_DECISION = "pending_decision"
    AWARDED = "awarded"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class ApplicationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GrantApplication(Base):
    """Grant application tracking."""
    __tablename__ = "grant_applications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    funder_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("funder_profiles.id"), nullable=True)

    # Basic Info
    application_name: Mapped[str] = mapped_column(String(255))
    funder_name: Mapped[str] = mapped_column(String(255))
    program_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Funding
    amount_requested: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount_awarded: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grant_period_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Matching/Cost Share
    match_required: Mapped[bool] = mapped_column(Boolean, default=False)
    match_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # cash, in-kind, both
    match_secured: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Stage and Status
    stage: Mapped[ApplicationStage] = mapped_column(Enum(ApplicationStage), default=ApplicationStage.PROSPECT)
    priority: Mapped[ApplicationPriority] = mapped_column(Enum(ApplicationPriority), default=ApplicationPriority.MEDIUM)
    probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100%

    # Key Dates
    opportunity_identified_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    loi_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    loi_submitted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    application_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_expected_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    project_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    project_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Team
    lead_writer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    team_members: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    internal_reviewer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Submission Details
    submission_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # online, email, mail
    portal_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmation_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Decision Info
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_received: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resubmission_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    resubmission_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks: Mapped[List["ApplicationTask"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    documents: Mapped[List["ApplicationDocument"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    stage_history: Mapped[List["StageHistory"]] = relationship(back_populates="application", cascade="all, delete-orphan")


class ApplicationTask(Base):
    """Tasks for grant application process."""
    __tablename__ = "application_tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_applications.id"))

    task_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), default="general")  # writing, review, document, submission, etc.

    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, completed, cancelled

    dependencies: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    application: Mapped["GrantApplication"] = relationship(back_populates="tasks")


class ApplicationDocument(Base):
    """Documents associated with grant application."""
    __tablename__ = "application_documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_applications.id"))

    document_name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(100))  # proposal, budget, narrative, attachment, etc.

    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, draft, final, submitted

    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_modified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application: Mapped["GrantApplication"] = relationship(back_populates="documents")


class StageHistory(Base):
    """History of application stage changes."""
    __tablename__ = "application_stage_history"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_applications.id"))

    from_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(50))
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    change_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    application: Mapped["GrantApplication"] = relationship(back_populates="stage_history")
