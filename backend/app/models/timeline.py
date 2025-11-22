"""Timeline and milestone models for project management."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class MilestoneStatus(enum.Enum):
    """Status of a milestone."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Milestone(Base):
    """Milestone model for project timeline management."""

    __tablename__ = "milestones"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Milestone details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.NOT_STARTED)

    # Dates
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Progress
    progress_percentage = Column(Float, default=0)
    order_index = Column(Integer, default=0)

    # Dependencies
    depends_on_id = Column(PGUUID(as_uuid=True), ForeignKey("milestones.id"), nullable=True)

    # Deliverables
    deliverables = Column(Text, nullable=True)  # JSON array of deliverable descriptions

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref="milestones")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan")
    depends_on = relationship("Milestone", remote_side=[id])


class Task(Base):
    """Task model for milestone tasks."""

    __tablename__ = "tasks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    milestone_id = Column(PGUUID(as_uuid=True), ForeignKey("milestones.id"), nullable=False)

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    is_completed = Column(Boolean, default=False)

    # Assignment
    assigned_to_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Dates
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Order
    order_index = Column(Integer, default=0)

    # Estimated time in hours
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    milestone = relationship("Milestone", back_populates="tasks")
    assigned_to = relationship("User", backref="assigned_tasks")


class ProjectPhase(Base):
    """Project phase model for high-level project timeline."""

    __tablename__ = "project_phases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Phase details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), default="#3B82F6")  # Hex color for UI

    # Dates
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Order
    order_index = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref="phases")
