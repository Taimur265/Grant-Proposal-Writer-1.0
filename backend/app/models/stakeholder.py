"""Stakeholder management models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class StakeholderType(enum.Enum):
    FUNDER = "funder"
    PARTNER = "partner"
    BENEFICIARY = "beneficiary"
    GOVERNMENT = "government"
    COMMUNITY = "community"
    BOARD_MEMBER = "board_member"
    STAFF = "staff"
    CONSULTANT = "consultant"
    EVALUATOR = "evaluator"
    VENDOR = "vendor"
    OTHER = "other"


class EngagementLevel(enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Stakeholder(Base):
    """Stakeholder entity model."""

    __tablename__ = "stakeholders"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(500))
    organization: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    stakeholder_type: Mapped[StakeholderType] = mapped_column(Enum(StakeholderType))

    # Contact info
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Engagement
    engagement_level: Mapped[EngagementLevel] = mapped_column(Enum(EngagementLevel), default=EngagementLevel.MEDIUM)
    influence_level: Mapped[str] = mapped_column(String(20), default="medium")  # high, medium, low
    interest_level: Mapped[str] = mapped_column(String(20), default="medium")

    # Relationship
    relationship_status: Mapped[str] = mapped_column(String(50), default="active")  # active, inactive, potential
    relationship_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Interests and needs
    interests: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    needs: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    expectations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Communication preferences
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    communication_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class StakeholderInteraction(Base):
    """Track interactions with stakeholders."""

    __tablename__ = "stakeholder_interactions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    stakeholder_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("stakeholders.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    interaction_type: Mapped[str] = mapped_column(String(50))  # meeting, call, email, event, etc.
    subject: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    interaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    follow_up_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attachments: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StakeholderCommitment(Base):
    """Track commitments from/to stakeholders."""

    __tablename__ = "stakeholder_commitments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    stakeholder_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("stakeholders.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    commitment_type: Mapped[str] = mapped_column(String(50))  # financial, in-kind, technical, advocacy
    description: Mapped[str] = mapped_column(Text)

    amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, confirmed, fulfilled, cancelled

    documentation: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
