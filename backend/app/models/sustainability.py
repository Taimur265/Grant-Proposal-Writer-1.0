"""Sustainability Planning models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class FundingSource(str, enum.Enum):
    GRANTS = "grants"
    INDIVIDUAL_DONORS = "individual_donors"
    CORPORATE_SPONSORS = "corporate_sponsors"
    EARNED_INCOME = "earned_income"
    GOVERNMENT_CONTRACTS = "government_contracts"
    MEMBERSHIP_FEES = "membership_fees"
    ENDOWMENT = "endowment"
    IN_KIND = "in_kind"
    OTHER = "other"


class SustainabilityPlan(Base):
    """Sustainability plan for a project."""
    __tablename__ = "sustainability_plans"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Vision
    sustainability_vision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_term_goals: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Current State
    current_annual_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_funding_sources: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Sustainability Analysis
    strengths: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    opportunities: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    threats: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Exit Strategy
    grant_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    transition_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_criteria: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Institutionalization
    institutionalization_strategy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_integration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_ownership_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    funding_strategies: Mapped[List["FundingStrategy"]] = relationship(back_populates="sustainability_plan", cascade="all, delete-orphan")
    capacity_elements: Mapped[List["CapacityElement"]] = relationship(back_populates="sustainability_plan", cascade="all, delete-orphan")


class FundingStrategy(Base):
    """Funding diversification strategies."""
    __tablename__ = "funding_strategies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    sustainability_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sustainability_plans.id"))

    funding_source: Mapped[FundingSource] = mapped_column(Enum(FundingSource))
    strategy_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Financial projections
    current_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_1_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_2_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_3_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Implementation
    key_activities: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    timeline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Risk assessment
    feasibility_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="planned")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    sustainability_plan: Mapped["SustainabilityPlan"] = relationship(back_populates="funding_strategies")


class CapacityElement(Base):
    """Capacity building elements for sustainability."""
    __tablename__ = "capacity_elements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    sustainability_plan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("sustainability_plans.id"))

    element_type: Mapped[str] = mapped_column(String(100))  # human, organizational, financial, technical
    element_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    current_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    development_activities: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    timeline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resources_needed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="planned")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    sustainability_plan: Mapped["SustainabilityPlan"] = relationship(back_populates="capacity_elements")
