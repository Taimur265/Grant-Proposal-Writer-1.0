"""Project model for organizing grant proposals."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Project(Base):
    """Project model for organizing grant proposals."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    grant_type = Column(String(100), nullable=True)  # federal, state, foundation, corporate
    funding_agency = Column(String(255), nullable=True)
    deadline = Column(DateTime, nullable=True)
    target_amount = Column(String(50), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)

    # Foreign Keys
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"
