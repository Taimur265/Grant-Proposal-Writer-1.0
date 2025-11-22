"""Team management models with roles and permissions."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class TeamRole(enum.Enum):
    """Team member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class InvitationStatus(enum.Enum):
    """Team invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Role permissions mapping
ROLE_PERMISSIONS = {
    TeamRole.OWNER: {
        "manage_team": True,
        "manage_project": True,
        "delete_project": True,
        "edit_proposal": True,
        "generate_proposal": True,
        "upload_documents": True,
        "delete_documents": True,
        "approve_workflow": True,
        "export": True,
        "view": True,
    },
    TeamRole.ADMIN: {
        "manage_team": True,
        "manage_project": True,
        "delete_project": False,
        "edit_proposal": True,
        "generate_proposal": True,
        "upload_documents": True,
        "delete_documents": True,
        "approve_workflow": True,
        "export": True,
        "view": True,
    },
    TeamRole.EDITOR: {
        "manage_team": False,
        "manage_project": False,
        "delete_project": False,
        "edit_proposal": True,
        "generate_proposal": True,
        "upload_documents": True,
        "delete_documents": False,
        "approve_workflow": False,
        "export": True,
        "view": True,
    },
    TeamRole.REVIEWER: {
        "manage_team": False,
        "manage_project": False,
        "delete_project": False,
        "edit_proposal": False,
        "generate_proposal": False,
        "upload_documents": False,
        "delete_documents": False,
        "approve_workflow": True,
        "export": True,
        "view": True,
    },
    TeamRole.VIEWER: {
        "manage_team": False,
        "manage_project": False,
        "delete_project": False,
        "edit_proposal": False,
        "generate_proposal": False,
        "upload_documents": False,
        "delete_documents": False,
        "approve_workflow": False,
        "export": False,
        "view": True,
    },
}


class Team(Base):
    """Team model for collaborative work."""

    __tablename__ = "teams"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Team info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Owner
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Settings
    default_role = Column(Enum(TeamRole), default=TeamRole.VIEWER)
    settings = Column(JSON, default={})

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Team membership model."""

    __tablename__ = "team_members"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Role and permissions
    role = Column(Enum(TeamRole), default=TeamRole.VIEWER)
    custom_permissions = Column(JSON, default={})  # Override default role permissions

    # Status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", backref="team_memberships")


class TeamInvitation(Base):
    """Team invitation model."""

    __tablename__ = "team_invitations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)

    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.VIEWER)
    message = Column(Text, nullable=True)

    # Token for accepting
    token = Column(String(100), nullable=False, unique=True)

    # Status
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    invited_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Dates
    expires_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id], backref="sent_invitations")
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])


class ProjectTeamAccess(Base):
    """Project-level team access."""

    __tablename__ = "project_team_access"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)

    # Access level
    access_role = Column(Enum(TeamRole), default=TeamRole.VIEWER)
    granted_by_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", backref="team_access")
    team = relationship("Team", backref="project_access")
    granted_by = relationship("User", backref="granted_access")
