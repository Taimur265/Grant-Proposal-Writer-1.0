"""Collaboration models for comments, sharing, and team features."""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class CommentType(enum.Enum):
    """Types of comments."""
    GENERAL = "general"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    REVISION = "revision"
    APPROVAL = "approval"


class CommentStatus(enum.Enum):
    """Status of a comment."""
    OPEN = "open"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SharePermission(enum.Enum):
    """Permission levels for shared access."""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class Comment(Base):
    """Comment model for discussions on proposals and documents."""

    __tablename__ = "comments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(Text, nullable=False)
    comment_type = Column(Enum(CommentType), default=CommentType.GENERAL)
    status = Column(Enum(CommentStatus), default=CommentStatus.OPEN)

    # Author
    author_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Target (polymorphic - can be on proposal, document, or project)
    target_type = Column(String(50), nullable=False)  # 'proposal', 'document', 'project'
    target_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Optional: specific section or position in the document
    section_id = Column(String(100), nullable=True)
    position_start = Column(Integer, nullable=True)
    position_end = Column(Integer, nullable=True)
    highlighted_text = Column(Text, nullable=True)

    # Threading
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    author = relationship("User", foreign_keys=[author_id], backref="comments")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    replies = relationship("Comment", backref="parent", remote_side=[id])


class ProjectShare(Base):
    """Model for sharing projects with other users."""

    __tablename__ = "project_shares"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    shared_with_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shared_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW)

    # Optional message when sharing
    message = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    accepted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", backref="shares")
    shared_with = relationship("User", foreign_keys=[shared_with_id])
    shared_by = relationship("User", foreign_keys=[shared_by_id])


class ActivityLog(Base):
    """Activity log for tracking all actions on projects."""

    __tablename__ = "activity_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Who performed the action
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # What was the action
    action = Column(String(100), nullable=False)  # e.g., 'created', 'updated', 'deleted', 'shared'
    action_details = Column(Text, nullable=True)  # JSON with additional details

    # Target of the action
    target_type = Column(String(50), nullable=False)  # 'project', 'document', 'proposal', 'comment'
    target_id = Column(PGUUID(as_uuid=True), nullable=False)
    target_name = Column(String(255), nullable=True)  # Cached name for display

    # Context
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="activity_logs")
    project = relationship("Project", backref="activity_logs")


class Notification(Base):
    """Notification model for user notifications."""

    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Recipient
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'comment', 'share', 'deadline', 'mention'

    # Link to relevant item
    link_type = Column(String(50), nullable=True)
    link_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="notifications")
