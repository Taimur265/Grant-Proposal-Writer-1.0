"""Funder Research and Discovery models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class FunderType(str, enum.Enum):
    FOUNDATION = "foundation"
    CORPORATION = "corporation"
    GOVERNMENT_FEDERAL = "government_federal"
    GOVERNMENT_STATE = "government_state"
    GOVERNMENT_LOCAL = "government_local"
    INDIVIDUAL = "individual"
    FAMILY_FOUNDATION = "family_foundation"
    COMMUNITY_FOUNDATION = "community_foundation"
    INTERNATIONAL = "international"


class FitScore(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class FunderProfile(Base):
    """Detailed funder profile for research."""
    __tablename__ = "funder_profiles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    name: Mapped[str] = mapped_column(String(255))
    funder_type: Mapped[FunderType] = mapped_column(Enum(FunderType))

    # Contact Information
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Key Contacts
    primary_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    program_officer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Funding Information
    total_annual_giving: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_grant_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grant_range_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grant_range_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Focus Areas
    focus_areas: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    geographic_focus: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    population_focus: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Priorities and Interests
    funding_priorities: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    strategic_initiatives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Eligibility
    eligible_org_types: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    eligibility_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    restrictions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Application Process
    application_process: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepts_unsolicited: Mapped[bool] = mapped_column(Boolean, default=True)
    loi_required: Mapped[bool] = mapped_column(Boolean, default=False)
    application_deadlines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Past Grants
    past_grantees: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    sample_grants: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Fit Assessment
    fit_score: Mapped[Optional[FitScore]] = mapped_column(Enum(FitScore), nullable=True)
    fit_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tracking
    last_researched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    grant_opportunities: Mapped[List["GrantOpportunity"]] = relationship(back_populates="funder", cascade="all, delete-orphan")
    cultivation_activities: Mapped[List["CultivationActivity"]] = relationship(back_populates="funder", cascade="all, delete-orphan")


class GrantOpportunity(Base):
    """Specific grant opportunity from a funder."""
    __tablename__ = "grant_opportunities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    funder_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("funder_profiles.id"))
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    opportunity_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rfp_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Funding Details
    funding_amount_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    funding_amount_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grant_duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Eligibility
    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_required: Mapped[bool] = mapped_column(Boolean, default=False)
    match_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timeline
    announcement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    loi_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    application_deadline: Mapped[datetime] = mapped_column(DateTime)
    award_notification_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    project_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Application Requirements
    application_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    required_documents: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    application_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Fit and Priority
    fit_score: Mapped[Optional[FitScore]] = mapped_column(Enum(FitScore), nullable=True)
    priority_level: Mapped[str] = mapped_column(String(20), default="medium")

    # Status
    status: Mapped[str] = mapped_column(String(50), default="identified")  # identified, researching, pursuing, applied, awarded, declined

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    funder: Mapped["FunderProfile"] = relationship(back_populates="grant_opportunities")


class CultivationActivity(Base):
    """Funder cultivation and stewardship activities."""
    __tablename__ = "cultivation_activities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    funder_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("funder_profiles.id"))
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    activity_type: Mapped[str] = mapped_column(String(100))  # meeting, call, email, event, site_visit, report
    activity_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activity_date: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    staff_involved: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    funder: Mapped["FunderProfile"] = relationship(back_populates="cultivation_activities")
