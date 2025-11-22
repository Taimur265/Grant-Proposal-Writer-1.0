"""Needs Assessment models for grant proposals."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class AssessmentType(str, enum.Enum):
    COMMUNITY = "community"
    ORGANIZATIONAL = "organizational"
    PROGRAM = "program"
    CAPACITY = "capacity"
    MARKET = "market"


class DataCollectionMethod(str, enum.Enum):
    SURVEY = "survey"
    INTERVIEW = "interview"
    FOCUS_GROUP = "focus_group"
    OBSERVATION = "observation"
    SECONDARY_DATA = "secondary_data"
    LITERATURE_REVIEW = "literature_review"
    ASSET_MAPPING = "asset_mapping"


class NeedsAssessment(Base):
    """Needs assessment for a project or community."""
    __tablename__ = "needs_assessments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    assessment_type: Mapped[AssessmentType] = mapped_column(Enum(AssessmentType))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Geographic scope
    geographic_area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    population_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timeline
    assessment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_collection_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_collection_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Methodology
    data_collection_methods: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Findings
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_findings: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    recommendations: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    identified_needs: Mapped[List["IdentifiedNeed"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    data_sources: Mapped[List["DataSource"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    community_assets: Mapped[List["CommunityAsset"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class IdentifiedNeed(Base):
    """Individual need identified in assessment."""
    __tablename__ = "identified_needs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("needs_assessments.id"))

    need_statement: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high, medium, low
    severity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10

    affected_population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    affected_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    current_services: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    service_gaps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_sources: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    proposed_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment: Mapped["NeedsAssessment"] = relationship(back_populates="identified_needs")


class DataSource(Base):
    """Data sources used in needs assessment."""
    __tablename__ = "assessment_data_sources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("needs_assessments.id"))

    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(100))  # primary, secondary
    collection_method: Mapped[DataCollectionMethod] = mapped_column(Enum(DataCollectionMethod))

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_collected: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    reliability_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    assessment: Mapped["NeedsAssessment"] = relationship(back_populates="data_sources")


class CommunityAsset(Base):
    """Community assets identified during assessment."""
    __tablename__ = "community_assets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("needs_assessments.id"))

    asset_name: Mapped[str] = mapped_column(String(255))
    asset_type: Mapped[str] = mapped_column(String(100))  # individual, organizational, institutional, physical, economic

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    potential_contribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    partnership_interest: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment: Mapped["NeedsAssessment"] = relationship(back_populates="community_assets")
