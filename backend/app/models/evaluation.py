"""Evaluation and M&E Framework models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class EvaluationType(str, enum.Enum):
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    PROCESS = "process"
    OUTCOME = "outcome"
    IMPACT = "impact"
    DEVELOPMENTAL = "developmental"


class EvaluationDesign(str, enum.Enum):
    EXPERIMENTAL = "experimental"
    QUASI_EXPERIMENTAL = "quasi_experimental"
    NON_EXPERIMENTAL = "non_experimental"
    MIXED_METHODS = "mixed_methods"
    PARTICIPATORY = "participatory"


class EvaluationPlan(Base):
    """Comprehensive evaluation plan for a project."""
    __tablename__ = "evaluation_plans"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Evaluation Framework
    evaluation_type: Mapped[EvaluationType] = mapped_column(Enum(EvaluationType))
    evaluation_design: Mapped[EvaluationDesign] = mapped_column(Enum(EvaluationDesign))
    theoretical_framework: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Purpose and Questions
    evaluation_purpose: Mapped[str] = mapped_column(Text)
    key_questions: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Stakeholders
    primary_users: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Who will use findings
    stakeholder_involvement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Budget
    evaluation_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Evaluator
    evaluator_type: Mapped[str] = mapped_column(String(50), default="internal")  # internal, external, mixed
    evaluator_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evaluator_qualifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ethical considerations
    irb_required: Mapped[bool] = mapped_column(Boolean, default=False)
    irb_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    consent_procedures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidentiality_measures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Limitations
    known_limitations: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Dissemination
    dissemination_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    data_collection_methods: Mapped[List["EvalDataCollection"]] = relationship(back_populates="evaluation_plan", cascade="all, delete-orphan")
    evaluation_indicators: Mapped[List["EvaluationIndicator"]] = relationship(back_populates="evaluation_plan", cascade="all, delete-orphan")


class EvalDataCollection(Base):
    """Data collection methods for evaluation."""
    __tablename__ = "eval_data_collection"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("evaluation_plans.id"))

    method_name: Mapped[str] = mapped_column(String(255))
    method_type: Mapped[str] = mapped_column(String(100))  # quantitative, qualitative, mixed

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # What it measures
    evaluation_questions_addressed: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    indicators_measured: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Sample
    target_population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sampling_strategy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Instruments
    instrument_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instrument_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # existing, adapted, developed
    validity_reliability: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeline
    collection_frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    collection_timeline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Responsibilities
    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Analysis
    analysis_approach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    evaluation_plan: Mapped["EvaluationPlan"] = relationship(back_populates="data_collection_methods")


class EvaluationIndicator(Base):
    """Indicators for evaluation."""
    __tablename__ = "evaluation_indicators"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    evaluation_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("evaluation_plans.id"))

    indicator_name: Mapped[str] = mapped_column(String(255))
    indicator_type: Mapped[str] = mapped_column(String(50))  # process, output, outcome, impact

    definition: Mapped[str] = mapped_column(Text)
    operational_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Measurement
    data_source: Mapped[str] = mapped_column(String(255))
    collection_method: Mapped[str] = mapped_column(String(255))
    frequency: Mapped[str] = mapped_column(String(100))

    baseline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target: Mapped[str] = mapped_column(String(255))

    disaggregation: Mapped[Optional[List]] = mapped_column(JSON, default=list)  # by gender, age, location, etc.

    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    evaluation_plan: Mapped["EvaluationPlan"] = relationship(back_populates="evaluation_indicators")


class DataCollectionSchedule(Base):
    """Schedule for data collection activities."""
    __tablename__ = "data_collection_schedules"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    activity_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    collection_type: Mapped[str] = mapped_column(String(100))  # baseline, midline, endline, ongoing

    scheduled_date: Mapped[datetime] = mapped_column(DateTime)
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    target_respondents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_respondents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
