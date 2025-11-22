"""Risk assessment and management models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class RiskCategory(enum.Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    EXTERNAL = "external"
    TECHNICAL = "technical"
    STAFFING = "staffing"


class RiskLikelihood(enum.Enum):
    RARE = "rare"  # 1
    UNLIKELY = "unlikely"  # 2
    POSSIBLE = "possible"  # 3
    LIKELY = "likely"  # 4
    ALMOST_CERTAIN = "almost_certain"  # 5


class RiskImpact(enum.Enum):
    INSIGNIFICANT = "insignificant"  # 1
    MINOR = "minor"  # 2
    MODERATE = "moderate"  # 3
    MAJOR = "major"  # 4
    CATASTROPHIC = "catastrophic"  # 5


class RiskStatus(enum.Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATING = "mitigating"
    MONITORING = "monitoring"
    CLOSED = "closed"
    REALIZED = "realized"


class Risk(Base):
    """Project risk model."""

    __tablename__ = "risks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))

    # Basic info
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[RiskCategory] = mapped_column(Enum(RiskCategory))
    status: Mapped[RiskStatus] = mapped_column(Enum(RiskStatus), default=RiskStatus.IDENTIFIED)

    # Assessment
    likelihood: Mapped[RiskLikelihood] = mapped_column(Enum(RiskLikelihood))
    impact: Mapped[RiskImpact] = mapped_column(Enum(RiskImpact))
    risk_score: Mapped[int] = mapped_column(Integer)  # likelihood * impact (1-25)

    # Risk owner
    owner_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Dates
    identified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Triggers and indicators
    triggers: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    early_warning_indicators: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Financial impact
    potential_cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    contingency_budget: Mapped[Optional[float]] = mapped_column(nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskMitigation(Base):
    """Risk mitigation strategy."""

    __tablename__ = "risk_mitigations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    risk_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"))

    strategy_type: Mapped[str] = mapped_column(String(50))  # avoid, transfer, mitigate, accept
    description: Mapped[str] = mapped_column(Text)

    # Action plan
    actions: Mapped[List[dict]] = mapped_column(JSON, default=[])
    responsible_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Timeline
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    target_completion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Effectiveness
    status: Mapped[str] = mapped_column(String(50), default="planned")  # planned, in_progress, completed, ineffective
    effectiveness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5

    # Residual risk after mitigation
    residual_likelihood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    residual_impact: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskReview(Base):
    """Periodic risk review record."""

    __tablename__ = "risk_reviews"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    risk_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"))
    reviewer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Updated assessment
    new_likelihood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_impact: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    findings: Mapped[str] = mapped_column(Text)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
