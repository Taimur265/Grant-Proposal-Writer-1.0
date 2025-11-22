"""Post-Award Grant Management models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class GrantStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    NO_COST_EXTENSION = "no_cost_extension"
    CLOSING = "closing"
    CLOSED = "closed"


class ReportType(str, enum.Enum):
    PROGRESS = "progress"
    FINANCIAL = "financial"
    NARRATIVE = "narrative"
    INTERIM = "interim"
    ANNUAL = "annual"
    FINAL = "final"
    CLOSEOUT = "closeout"


class AwardedGrant(Base):
    """Awarded grant for post-award management."""
    __tablename__ = "awarded_grants"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    application_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_applications.id"), nullable=True)

    # Grant Details
    grant_title: Mapped[str] = mapped_column(String(255))
    funder_name: Mapped[str] = mapped_column(String(255))
    grant_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cfda_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Federal grants

    # Funding
    total_award_amount: Mapped[float] = mapped_column(Float)
    amount_received: Mapped[float] = mapped_column(Float, default=0)
    amount_remaining: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Indirect costs
    indirect_cost_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    indirect_cost_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Cost share
    cost_share_required: Mapped[bool] = mapped_column(Boolean, default=False)
    cost_share_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_share_met: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timeline
    award_date: Mapped[datetime] = mapped_column(DateTime)
    project_start_date: Mapped[datetime] = mapped_column(DateTime)
    project_end_date: Mapped[datetime] = mapped_column(DateTime)
    original_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # If extended

    # Contacts
    funder_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    funder_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    funder_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    program_officer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    grants_manager: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Internal
    project_director: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fiscal_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[GrantStatus] = mapped_column(Enum(GrantStatus), default=GrantStatus.ACTIVE)

    # Terms and Conditions
    special_conditions: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    compliance_requirements: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reporting_requirements: Mapped[List["ReportingRequirement"]] = relationship(back_populates="grant", cascade="all, delete-orphan")
    expenditures: Mapped[List["GrantExpenditure"]] = relationship(back_populates="grant", cascade="all, delete-orphan")
    modifications: Mapped[List["GrantModification"]] = relationship(back_populates="grant", cascade="all, delete-orphan")
    deliverables: Mapped[List["GrantDeliverable"]] = relationship(back_populates="grant", cascade="all, delete-orphan")


class ReportingRequirement(Base):
    """Reporting requirements for awarded grants."""
    __tablename__ = "reporting_requirements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    grant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("awarded_grants.id"))

    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType))
    report_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Schedule
    frequency: Mapped[str] = mapped_column(String(50))  # monthly, quarterly, annually, one-time
    due_date: Mapped[datetime] = mapped_column(DateTime)
    reporting_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reporting_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Submission
    submission_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submission_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, submitted, accepted, revision_requested
    submitted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Responsible party
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # File
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confirmation_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    grant: Mapped["AwardedGrant"] = relationship(back_populates="reporting_requirements")


class GrantExpenditure(Base):
    """Track grant expenditures."""
    __tablename__ = "grant_expenditures"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    grant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("awarded_grants.id"))

    budget_category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))

    budgeted_amount: Mapped[float] = mapped_column(Float)
    spent_amount: Mapped[float] = mapped_column(Float, default=0)
    encumbered_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    remaining_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Period
    fiscal_year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quarter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    grant: Mapped["AwardedGrant"] = relationship(back_populates="expenditures")


class GrantModification(Base):
    """Grant modifications and amendments."""
    __tablename__ = "grant_modifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    grant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("awarded_grants.id"))

    modification_type: Mapped[str] = mapped_column(String(100))  # budget_revision, no_cost_extension, scope_change, key_personnel
    description: Mapped[str] = mapped_column(Text)

    # Request details
    request_date: Mapped[datetime] = mapped_column(DateTime)
    requested_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Approval
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, approved, denied
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    funder_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Impact
    budget_impact: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timeline_impact_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Documentation
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    grant: Mapped["AwardedGrant"] = relationship(back_populates="modifications")


class GrantDeliverable(Base):
    """Grant deliverables tracking."""
    __tablename__ = "grant_deliverables"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    grant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("awarded_grants.id"))

    deliverable_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliverable_type: Mapped[str] = mapped_column(String(100))  # report, product, event, training, publication

    due_date: Mapped[datetime] = mapped_column(DateTime)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    responsible_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")
    quality_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    grant: Mapped["AwardedGrant"] = relationship(back_populates="deliverables")


class ImpactStory(Base):
    """Impact stories and testimonials."""
    __tablename__ = "impact_stories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    grant_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("awarded_grants.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    story_type: Mapped[str] = mapped_column(String(50))  # success_story, testimonial, case_study

    # Content
    summary: Mapped[str] = mapped_column(Text)
    full_story: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quote_attribution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Subject
    beneficiary_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Can be anonymized
    beneficiary_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    demographics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Impact data
    quantitative_impact: Mapped[Optional[List]] = mapped_column(JSON, default=list)  # Measurable outcomes
    qualitative_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Media
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    has_media_release: Mapped[bool] = mapped_column(Boolean, default=False)

    # Usage
    tags: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    suitable_for: Mapped[Optional[List]] = mapped_column(JSON, default=list)  # website, annual_report, proposals, social_media
    last_used_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # Approval
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    story_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
