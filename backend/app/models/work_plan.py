"""Work Plan and Gantt Chart models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class WorkPlan(Base):
    """Project work plan."""
    __tablename__ = "work_plans"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Project timeline
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)

    # Budget
    total_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Settings
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)  # 1=January, 7=July, etc.
    show_weekends: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(50), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    phases: Mapped[List["WorkPlanPhase"]] = relationship(back_populates="work_plan", cascade="all, delete-orphan")
    milestones: Mapped[List["WorkPlanMilestone"]] = relationship(back_populates="work_plan", cascade="all, delete-orphan")


class WorkPlanPhase(Base):
    """Phase/major component of work plan."""
    __tablename__ = "work_plan_phases"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    work_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("work_plans.id"))

    phase_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)

    # Color for visualization
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    work_plan: Mapped["WorkPlan"] = relationship(back_populates="phases")
    activities: Mapped[List["WorkPlanActivity"]] = relationship(back_populates="phase", cascade="all, delete-orphan")


class WorkPlanActivity(Base):
    """Activity/task in work plan."""
    __tablename__ = "work_plan_activities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    phase_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("work_plan_phases.id"))
    objective_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("objectives.id"), nullable=True)

    activity_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeline
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Duration
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Dependencies
    predecessors: Mapped[Optional[List]] = mapped_column(JSON, default=list)  # List of activity IDs
    dependency_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # FS, FF, SS, SF

    # Resources
    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    team_members: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Budget
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Deliverables
    deliverables: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Progress
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    progress_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Priority
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    is_critical_path: Mapped[bool] = mapped_column(Boolean, default=False)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    phase: Mapped["WorkPlanPhase"] = relationship(back_populates="activities")
    sub_tasks: Mapped[List["WorkPlanSubTask"]] = relationship(back_populates="activity", cascade="all, delete-orphan")


class WorkPlanSubTask(Base):
    """Sub-task under an activity."""
    __tablename__ = "work_plan_sub_tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("work_plan_activities.id"))

    task_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    activity: Mapped["WorkPlanActivity"] = relationship(back_populates="sub_tasks")


class WorkPlanMilestone(Base):
    """Milestone in work plan."""
    __tablename__ = "work_plan_milestones"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    work_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("work_plans.id"))

    milestone_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    due_date: Mapped[datetime] = mapped_column(DateTime)
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    deliverables: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    is_reporting_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    report_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, completed, overdue

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    work_plan: Mapped["WorkPlan"] = relationship(back_populates="milestones")
