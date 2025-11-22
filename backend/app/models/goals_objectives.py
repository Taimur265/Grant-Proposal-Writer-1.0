"""SMART Goals and Objectives models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class GoalType(str, enum.Enum):
    STRATEGIC = "strategic"
    PROGRAMMATIC = "programmatic"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"


class ObjectiveStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Goal(Base):
    """High-level goal for a project."""
    __tablename__ = "goals"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_type: Mapped[GoalType] = mapped_column(Enum(GoalType), default=GoalType.PROGRAMMATIC)

    # Alignment
    aligned_with_mission: Mapped[bool] = mapped_column(Boolean, default=True)
    mission_alignment_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    funder_priority_alignment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeline
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Progress
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="active")

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    objectives: Mapped[List["Objective"]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class Objective(Base):
    """SMART objective under a goal."""
    __tablename__ = "objectives"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("goals.id"))

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SMART Components
    specific_statement: Mapped[str] = mapped_column(Text)  # What exactly will be accomplished?

    # Measurable
    measurement_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Achievable
    achievability_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resources_required: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    potential_barriers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relevant
    relevance_to_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevance_to_needs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Time-bound
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    milestones: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Status tracking
    status: Mapped[ObjectiveStatus] = mapped_column(Enum(ObjectiveStatus), default=ObjectiveStatus.NOT_STARTED)
    progress_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Responsible party
    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    responsible_team: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    goal: Mapped["Goal"] = relationship(back_populates="objectives")
    activities: Mapped[List["ObjectiveActivity"]] = relationship(back_populates="objective", cascade="all, delete-orphan")
    indicators: Mapped[List["PerformanceIndicator"]] = relationship(back_populates="objective", cascade="all, delete-orphan")


class ObjectiveActivity(Base):
    """Activities to achieve an objective."""
    __tablename__ = "objective_activities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    objective_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("objectives.id"))

    activity_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resources_needed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    deliverables: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(50), default="pending")
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    objective: Mapped["Objective"] = relationship(back_populates="activities")


class PerformanceIndicator(Base):
    """Performance indicators for objectives."""
    __tablename__ = "performance_indicators"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    objective_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("objectives.id"))

    indicator_name: Mapped[str] = mapped_column(String(255))
    indicator_type: Mapped[str] = mapped_column(String(50))  # output, outcome, impact

    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    target_value: Mapped[float] = mapped_column(Float)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_measured_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    unit_of_measure: Mapped[str] = mapped_column(String(100))
    frequency_of_measurement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_collection_method: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    objective: Mapped["Objective"] = relationship(back_populates="indicators")
