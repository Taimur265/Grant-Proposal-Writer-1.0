"""Logic model and theory of change models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class LogicModel(Base):
    """Project logic model / theory of change."""

    __tablename__ = "logic_models"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Problem/Need
    problem_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_causes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Theory of Change narrative
    theory_of_change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assumptions
    assumptions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    external_factors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Visual layout
    layout_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class LogicModelInput(Base):
    """Inputs/Resources for the logic model."""

    __tablename__ = "logic_model_inputs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    logic_model_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logic_models.id", ondelete="CASCADE"))

    category: Mapped[str] = mapped_column(String(100))  # funding, staff, equipment, partnerships, etc.
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planned")  # planned, secured, at_risk

    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LogicModelActivity(Base):
    """Activities in the logic model."""

    __tablename__ = "logic_model_activities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    logic_model_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logic_models.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)

    # Linked inputs
    input_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Implementation details
    frequency: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    target_participants: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    responsible_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LogicModelOutput(Base):
    """Outputs in the logic model."""

    __tablename__ = "logic_model_outputs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    logic_model_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logic_models.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)

    # What this output measures
    indicator: Mapped[str] = mapped_column(String(500))
    target: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Linked activities
    activity_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LogicModelOutcome(Base):
    """Outcomes in the logic model."""

    __tablename__ = "logic_model_outcomes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    logic_model_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logic_models.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)

    timeframe: Mapped[str] = mapped_column(String(50))  # short_term, medium_term, long_term

    # Indicator and measurement
    indicator: Mapped[str] = mapped_column(String(500))
    target: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Linked outputs
    output_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LogicModelImpact(Base):
    """Long-term impacts in the logic model."""

    __tablename__ = "logic_model_impacts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    logic_model_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("logic_models.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)

    # How it will be measured
    indicator: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    evaluation_approach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Linked outcomes
    outcome_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
