"""Reporting and metrics models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class ReportType(enum.Enum):
    PROGRESS = "progress"
    FINANCIAL = "financial"
    OUTCOME = "outcome"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    FINAL = "final"
    INTERIM = "interim"
    CUSTOM = "custom"


class ReportStatus(enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REVISION_REQUIRED = "revision_required"


class MetricType(enum.Enum):
    OUTPUT = "output"
    OUTCOME = "outcome"
    IMPACT = "impact"
    PROCESS = "process"
    FINANCIAL = "financial"


class Report(Base):
    """Grant report model."""

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    proposal_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("proposals.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType))
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.DRAFT)

    # Reporting period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Content sections
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activities_completed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectives_progress: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    challenges: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Financial section
    budget_spent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_remaining: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    financial_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expenditure_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Metrics summary
    metrics_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Submission
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_to: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Attachments
    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    # Review
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revision_history: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Metric(Base):
    """Project metric/indicator model."""

    __tablename__ = "metrics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType))

    # Target and measurement
    unit: Mapped[str] = mapped_column(String(100))  # e.g., "people", "sessions", "dollars"
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_value: Mapped[float] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float, default=0)

    # Data collection
    data_source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    collection_method: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    collection_frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # monthly, quarterly, etc.
    responsible_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Progress tracking
    progress_percentage: Mapped[float] = mapped_column(Float, default=0)
    on_track: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricDataPoint(Base):
    """Historical data points for metrics."""

    __tablename__ = "metric_data_points"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("metrics.id", ondelete="CASCADE"))

    value: Mapped[float] = mapped_column(Float)
    recorded_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)  # Links to supporting documents

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class KPIDashboard(Base):
    """User's KPI dashboard configuration."""

    __tablename__ = "kpi_dashboards"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # KPIs to display
    metric_ids: Mapped[List[str]] = mapped_column(JSON, default=[])
    layout_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    refresh_interval: Mapped[int] = mapped_column(Integer, default=300)  # seconds

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
