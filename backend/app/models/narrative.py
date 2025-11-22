"""Narrative and Proposal Section Builder models."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class SectionType(str, enum.Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    ORGANIZATION_BACKGROUND = "organization_background"
    STATEMENT_OF_NEED = "statement_of_need"
    PROJECT_DESCRIPTION = "project_description"
    GOALS_OBJECTIVES = "goals_objectives"
    METHODOLOGY = "methodology"
    TIMELINE = "timeline"
    EVALUATION_PLAN = "evaluation_plan"
    SUSTAINABILITY = "sustainability"
    ORGANIZATIONAL_CAPACITY = "organizational_capacity"
    BUDGET_NARRATIVE = "budget_narrative"
    CONCLUSION = "conclusion"
    APPENDICES = "appendices"
    CUSTOM = "custom"


class ProposalNarrative(Base):
    """Complete proposal narrative structure."""
    __tablename__ = "proposal_narratives"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    proposal_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("proposals.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    funder_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Format requirements
    max_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_words: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    font_requirements: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    margin_requirements: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Current stats
    current_word_count: Mapped[int] = mapped_column(Integer, default=0)
    current_page_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(50), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sections: Mapped[List["NarrativeSection"]] = relationship(back_populates="narrative", cascade="all, delete-orphan")


class NarrativeSection(Base):
    """Individual section of proposal narrative."""
    __tablename__ = "narrative_sections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    narrative_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("proposal_narratives.id"))

    section_type: Mapped[SectionType] = mapped_column(Enum(SectionType))
    title: Mapped[str] = mapped_column(String(255))
    custom_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guidance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Instructions for this section
    funder_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Requirements
    max_words: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_characters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    # Current stats
    current_word_count: Mapped[int] = mapped_column(Integer, default=0)
    current_character_count: Mapped[int] = mapped_column(Integer, default=0)

    # Writing tips
    writing_tips: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    key_points_to_include: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    common_mistakes: Mapped[Optional[List]] = mapped_column(JSON, default=list)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="not_started")  # not_started, in_progress, draft, review, final
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    narrative: Mapped["ProposalNarrative"] = relationship(back_populates="sections")
    revisions: Mapped[List["SectionRevision"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class SectionRevision(Base):
    """Revision history for narrative sections."""
    __tablename__ = "section_revisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("narrative_sections.id"))

    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    revision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    section: Mapped["NarrativeSection"] = relationship(back_populates="revisions")


class BoilerplateText(Base):
    """Reusable boilerplate text library."""
    __tablename__ = "boilerplate_texts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))  # organization, mission, history, capacity, etc.
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    content: Mapped[str] = mapped_column(Text)

    # Usage tracking
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)

    # Versions for different lengths
    short_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 50-100 words
    medium_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 100-250 words
    long_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 250+ words

    tags: Mapped[Optional[List]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BudgetJustification(Base):
    """Budget justification narrative."""
    __tablename__ = "budget_justifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    budget_category: Mapped[str] = mapped_column(String(100))  # personnel, fringe, travel, equipment, supplies, etc.
    line_item: Mapped[str] = mapped_column(String(255))

    amount: Mapped[float] = mapped_column(Float)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    justification: Mapped[str] = mapped_column(Text)  # Why is this needed?
    calculation_basis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # How was cost calculated?

    is_grant_funded: Mapped[bool] = mapped_column(Boolean, default=True)
    match_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
