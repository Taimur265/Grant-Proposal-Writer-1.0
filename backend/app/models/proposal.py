"""Proposal model for storing generated grant proposals."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, Integer, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ProposalStatus(str, enum.Enum):
    """Proposal status enumeration."""
    GENERATING = "generating"
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    FINAL = "final"
    SUBMITTED = "submitted"


class Proposal(Base):
    """Proposal model for storing generated grant proposals."""

    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    version = Column(Integer, default=1)
    status = Column(Enum(ProposalStatus), default=ProposalStatus.DRAFT)

    # Content
    executive_summary = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    structured_content = Column(JSON, nullable=True)  # JSON structure of sections

    # Metadata
    word_count = Column(Integer, nullable=True)
    compliance_score = Column(Float, nullable=True)  # How well it matches guidelines
    ai_model_used = Column(String(100), nullable=True)
    generation_params = Column(JSON, nullable=True)

    # Export information
    last_exported_at = Column(DateTime, nullable=True)
    export_format = Column(String(20), nullable=True)

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="proposals")
    creator = relationship("User", foreign_keys=[created_by])
    sections = relationship("ProposalSection", back_populates="proposal", cascade="all, delete-orphan")
    feedback = relationship("ProposalFeedback", back_populates="proposal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Proposal {self.title}>"


class ProposalSection(Base):
    """Individual sections of a proposal."""

    __tablename__ = "proposal_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_name = Column(String(255), nullable=False)
    section_order = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    max_words = Column(Integer, nullable=True)  # From guidelines
    is_required = Column(Boolean, default=True)
    is_complete = Column(Boolean, default=False)

    # AI assistance
    ai_suggestions = Column(JSON, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    # Foreign Keys
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    proposal = relationship("Proposal", back_populates="sections")

    def __repr__(self):
        return f"<ProposalSection {self.section_name}>"


# Import Boolean for ProposalSection
from sqlalchemy import Boolean


class ProposalFeedback(Base):
    """Feedback and comments on proposals."""

    __tablename__ = "proposal_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("proposal_sections.id"), nullable=True)
    feedback_type = Column(String(50), nullable=False)  # comment, suggestion, approval, rejection
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)

    # Foreign Keys
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    proposal = relationship("Proposal", back_populates="feedback")
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<ProposalFeedback {self.feedback_type}>"
