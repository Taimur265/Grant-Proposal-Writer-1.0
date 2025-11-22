"""Resource library and boilerplate text models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class ResourceType(enum.Enum):
    BOILERPLATE = "boilerplate"
    TEMPLATE = "template"
    SAMPLE = "sample"
    REFERENCE = "reference"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    FORM = "form"


class ResourceCategory(enum.Enum):
    ORGANIZATION = "organization"
    BUDGET = "budget"
    EVALUATION = "evaluation"
    METHODOLOGY = "methodology"
    SUSTAINABILITY = "sustainability"
    CAPACITY = "capacity"
    DIVERSITY = "diversity"
    COMPLIANCE = "compliance"
    OTHER = "other"


class Resource(Base):
    """Reusable resource/boilerplate text."""

    __tablename__ = "resources"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    resource_type: Mapped[ResourceType] = mapped_column(Enum(ResourceType))
    category: Mapped[ResourceCategory] = mapped_column(Enum(ResourceCategory))

    content: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    funder_types: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # federal, foundation, etc.
    grant_types: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Usage tracking
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sharing
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    shared_with_team: Mapped[bool] = mapped_column(Boolean, default=False)

    # Review status
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ResourceUsage(Base):
    """Track where resources are used."""

    __tablename__ = "resource_usages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"))
    proposal_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("proposals.id", ondelete="SET NULL"), nullable=True)

    used_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    section_used_in: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    was_modified: Mapped[bool] = mapped_column(Boolean, default=False)


class Checklist(Base):
    """Reusable checklist template."""

    __tablename__ = "checklists"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checklist_type: Mapped[str] = mapped_column(String(100))  # pre_submission, review, compliance, etc.

    items: Mapped[List[dict]] = mapped_column(JSON, default=[])  # [{text, required, order}]

    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ChecklistInstance(Base):
    """Instance of a checklist for a project/proposal."""

    __tablename__ = "checklist_instances"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    checklist_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("checklists.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    proposal_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))

    # Items with completion status
    items: Mapped[List[dict]] = mapped_column(JSON, default=[])  # [{text, required, completed, completed_by, completed_at, notes}]

    completion_percentage: Mapped[float] = mapped_column(default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class FundingHistory(Base):
    """Organization's funding history for reuse."""

    __tablename__ = "funding_history"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    funder_name: Mapped[str] = mapped_column(String(500))
    grant_title: Mapped[str] = mapped_column(String(500))
    grant_number: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    amount: Mapped[float] = mapped_column()
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(50))  # completed, active, terminated
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    can_use_as_reference: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
