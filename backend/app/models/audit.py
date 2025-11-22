"""Audit logging models."""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET

from app.database import Base


class AuditAction(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    SHARE = "share"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    GENERATE = "generate"
    INVITE = "invite"
    PERMISSION_CHANGE = "permission_change"


class ResourceType(enum.Enum):
    USER = "user"
    PROJECT = "project"
    PROPOSAL = "proposal"
    DOCUMENT = "document"
    BUDGET = "budget"
    TEAM = "team"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    FUNDER = "funder"
    OPPORTUNITY = "opportunity"
    CALENDAR_EVENT = "calendar_event"
    LETTER = "letter"
    SETTINGS = "settings"
    COMMENT = "comment"


class AuditLog(Base):
    """Audit log for tracking all system activities."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Who performed the action
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Preserved even if user deleted

    # What action was performed
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction))
    action_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # What resource was affected
    resource_type: Mapped[ResourceType] = mapped_column(Enum(ResourceType))
    resource_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Parent resource (for nested resources)
    parent_resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    parent_resource_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Details of the change
    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Diff of changes

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_action', 'action'),
        Index('ix_audit_logs_resource_type', 'resource_type'),
        Index('ix_audit_logs_resource_id', 'resource_id'),
        Index('ix_audit_logs_created_at', 'created_at'),
        Index('ix_audit_logs_user_action', 'user_id', 'action'),
    )


class AccessLog(Base):
    """Track document and resource access."""

    __tablename__ = "access_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    resource_type: Mapped[ResourceType] = mapped_column(Enum(ResourceType))
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))

    access_type: Mapped[str] = mapped_column(String(50))  # view, edit, download, etc.
    duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index('ix_access_logs_resource', 'resource_type', 'resource_id'),
        Index('ix_access_logs_user', 'user_id'),
    )


class SecurityEvent(Base):
    """Track security-related events."""

    __tablename__ = "security_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    event_type: Mapped[str] = mapped_column(String(100))  # login_success, login_failure, password_change, etc.
    severity: Mapped[str] = mapped_column(String(20), default="info")  # info, warning, critical

    description: Mapped[str] = mapped_column(Text)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Geo location if available

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index('ix_security_events_type', 'event_type'),
        Index('ix_security_events_severity', 'severity'),
        Index('ix_security_events_user', 'user_id'),
    )
