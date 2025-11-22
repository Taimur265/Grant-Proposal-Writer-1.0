"""Funder database models for grant opportunities."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class FunderType(enum.Enum):
    """Types of funders."""
    FEDERAL = "federal"
    STATE = "state"
    FOUNDATION = "foundation"
    CORPORATE = "corporate"
    INTERNATIONAL = "international"
    NONPROFIT = "nonprofit"
    OTHER = "other"


class OpportunityStatus(enum.Enum):
    """Status of grant opportunities."""
    OPEN = "open"
    CLOSING_SOON = "closing_soon"
    CLOSED = "closed"
    UPCOMING = "upcoming"
    ROLLING = "rolling"


class ApplicationStatus(enum.Enum):
    """Status of grant applications."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class Funder(Base):
    """Funder/Grantor organization model."""

    __tablename__ = "funders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic info
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)
    funder_type = Column(Enum(FunderType), default=FunderType.FOUNDATION)
    description = Column(Text, nullable=True)

    # Contact info
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    # Funding info
    focus_areas = Column(ARRAY(String), default=[])
    geographic_focus = Column(ARRAY(String), default=[])
    eligible_organizations = Column(ARRAY(String), default=[])
    typical_award_min = Column(Float, nullable=True)
    typical_award_max = Column(Float, nullable=True)
    total_annual_giving = Column(Float, nullable=True)

    # Requirements
    indirect_cost_policy = Column(String(255), nullable=True)
    max_indirect_rate = Column(Float, nullable=True)
    application_requirements = Column(JSON, default={})

    # Status
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # User who added
    added_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    opportunities = relationship("GrantOpportunity", back_populates="funder", cascade="all, delete-orphan")
    added_by = relationship("User", backref="added_funders")


class GrantOpportunity(Base):
    """Grant opportunity/program model."""

    __tablename__ = "grant_opportunities"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    funder_id = Column(PGUUID(as_uuid=True), ForeignKey("funders.id"), nullable=False)

    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    program_url = Column(String(500), nullable=True)
    opportunity_number = Column(String(100), nullable=True)

    # Funding details
    award_floor = Column(Float, nullable=True)
    award_ceiling = Column(Float, nullable=True)
    expected_awards = Column(Integer, nullable=True)
    total_funding = Column(Float, nullable=True)
    cost_sharing_required = Column(Boolean, default=False)
    cost_sharing_percentage = Column(Float, nullable=True)

    # Eligibility
    eligible_applicants = Column(ARRAY(String), default=[])
    eligibility_notes = Column(Text, nullable=True)

    # Dates
    posted_date = Column(DateTime, nullable=True)
    open_date = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    estimated_award_date = Column(DateTime, nullable=True)
    project_start_date = Column(DateTime, nullable=True)
    project_duration_months = Column(Integer, nullable=True)

    # Status
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.OPEN)

    # Categories
    focus_areas = Column(ARRAY(String), default=[])
    keywords = Column(ARRAY(String), default=[])

    # Requirements
    required_documents = Column(JSON, default=[])
    page_limits = Column(JSON, default={})
    submission_method = Column(String(100), nullable=True)

    # Notes
    internal_notes = Column(Text, nullable=True)
    is_bookmarked = Column(Boolean, default=False)
    match_score = Column(Float, nullable=True)  # Compatibility score with organization

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    funder = relationship("Funder", back_populates="opportunities")
    applications = relationship("GrantApplication", back_populates="opportunity", cascade="all, delete-orphan")


class GrantApplication(Base):
    """Grant application tracking model."""

    __tablename__ = "grant_applications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id = Column(PGUUID(as_uuid=True), ForeignKey("grant_opportunities.id"), nullable=False)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Application info
    application_title = Column(String(500), nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    requested_amount = Column(Float, nullable=True)
    awarded_amount = Column(Float, nullable=True)

    # Dates
    submission_date = Column(DateTime, nullable=True)
    notification_date = Column(DateTime, nullable=True)
    decision_date = Column(DateTime, nullable=True)

    # Tracking
    confirmation_number = Column(String(100), nullable=True)
    reviewer_feedback = Column(Text, nullable=True)
    score = Column(Float, nullable=True)

    # Notes
    internal_notes = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    opportunity = relationship("GrantOpportunity", back_populates="applications")
    project = relationship("Project", backref="applications")
    user = relationship("User", backref="grant_applications")


class FunderContact(Base):
    """Funder contact person model."""

    __tablename__ = "funder_contacts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    funder_id = Column(PGUUID(as_uuid=True), ForeignKey("funders.id"), nullable=False)

    # Contact info
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    funder = relationship("Funder", backref="contacts")
