"""Team management API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models.user import User
from app.models.team import Team, TeamMember, TeamInvitation, ProjectTeamAccess, TeamRole, ROLE_PERMISSIONS
from app.routers.auth import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])


# Schemas
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamInvite(BaseModel):
    email: EmailStr
    role: TeamRole = TeamRole.VIEWER
    message: Optional[str] = None


class ProjectAccessGrant(BaseModel):
    project_id: UUID
    can_edit: bool = False
    can_comment: bool = True
    can_export: bool = True


class MemberRoleUpdate(BaseModel):
    role: TeamRole


# Helper functions
async def get_team_member(
    db: AsyncSession, team_id: UUID, user_id: UUID
) -> Optional[TeamMember]:
    """Get team member record."""
    result = await db.execute(
        select(TeamMember).where(
            and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
    )
    return result.scalar_one_or_none()


async def check_permission(
    db: AsyncSession, team_id: UUID, user_id: UUID, permission: str
) -> bool:
    """Check if user has specific permission in team."""
    member = await get_team_member(db, team_id, user_id)
    if not member:
        return False

    role_permissions = ROLE_PERMISSIONS.get(member.role, {})
    return role_permissions.get(permission, False)


# Team endpoints
@router.post("/")
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team."""
    team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=current_user.id,
    )
    db.add(team)
    await db.flush()

    # Add creator as owner
    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
        invited_by_id=current_user.id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(team)

    return {
        "id": str(team.id),
        "name": team.name,
        "description": team.description,
    }


@router.get("/")
async def list_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List teams the user belongs to."""
    result = await db.execute(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == current_user.id)
    )

    teams = []
    for team in result.scalars():
        member = await get_team_member(db, team.id, current_user.id)
        teams.append({
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "role": member.role.value if member else None,
            "member_count": await get_team_member_count(db, team.id),
        })

    return {"teams": teams}


async def get_team_member_count(db: AsyncSession, team_id: UUID) -> int:
    """Get count of team members."""
    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id)
    )
    return len(result.scalars().all())


@router.get("/{team_id}")
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team details."""
    member = await get_team_member(db, team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")

    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get all members
    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id)
    )

    members = []
    for m in result.scalars():
        user = await db.get(User, m.user_id)
        members.append({
            "id": str(m.id),
            "user_id": str(m.user_id),
            "email": user.email if user else None,
            "name": user.name if user else None,
            "role": m.role.value,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        })

    return {
        "id": str(team.id),
        "name": team.name,
        "description": team.description,
        "owner_id": str(team.owner_id),
        "members": members,
        "created_at": team.created_at.isoformat(),
    }


@router.patch("/{team_id}")
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update team details."""
    if not await check_permission(db, team_id, current_user.id, "manage_team"):
        raise HTTPException(status_code=403, detail="Not authorized")

    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team_data.name:
        team.name = team_data.name
    if team_data.description is not None:
        team.description = team_data.description

    await db.commit()
    return {"message": "Team updated"}


@router.delete("/{team_id}")
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a team."""
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete team")

    await db.delete(team)
    await db.commit()
    return {"message": "Team deleted"}


# Team member management
@router.post("/{team_id}/invite")
async def invite_member(
    team_id: UUID,
    invite_data: TeamInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a user to the team."""
    if not await check_permission(db, team_id, current_user.id, "manage_team"):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if already a member
    result = await db.execute(
        select(User).where(User.email == invite_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        existing_member = await get_team_member(db, team_id, existing_user.id)
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a team member")

    # Create invitation
    invitation = TeamInvitation(
        team_id=team_id,
        email=invite_data.email,
        role=invite_data.role,
        invited_by_id=current_user.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=7),
        message=invite_data.message,
    )
    db.add(invitation)
    await db.commit()

    return {
        "message": "Invitation sent",
        "invitation_id": str(invitation.id),
        "token": invitation.token,
    }


@router.get("/{team_id}/invitations")
async def list_invitations(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pending invitations."""
    if not await check_permission(db, team_id, current_user.id, "manage_team"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(TeamInvitation).where(
            and_(
                TeamInvitation.team_id == team_id,
                TeamInvitation.accepted_at.is_(None),
                TeamInvitation.expires_at > datetime.utcnow(),
            )
        )
    )

    invitations = []
    for inv in result.scalars():
        invitations.append({
            "id": str(inv.id),
            "email": inv.email,
            "role": inv.role.value,
            "created_at": inv.created_at.isoformat(),
            "expires_at": inv.expires_at.isoformat(),
        })

    return {"invitations": invitations}


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a team invitation."""
    result = await db.execute(
        select(TeamInvitation).where(
            and_(
                TeamInvitation.token == token,
                TeamInvitation.accepted_at.is_(None),
                TeamInvitation.expires_at > datetime.utcnow(),
            )
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")

    if invitation.email != current_user.email:
        raise HTTPException(status_code=403, detail="Invitation is for a different email")

    # Add member
    member = TeamMember(
        team_id=invitation.team_id,
        user_id=current_user.id,
        role=invitation.role,
        invited_by_id=invitation.invited_by_id,
    )
    db.add(member)

    invitation.accepted_at = datetime.utcnow()
    await db.commit()

    return {"message": "Invitation accepted", "team_id": str(invitation.team_id)}


@router.patch("/{team_id}/members/{member_id}/role")
async def update_member_role(
    team_id: UUID,
    member_id: UUID,
    role_data: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a team member's role."""
    if not await check_permission(db, team_id, current_user.id, "manage_team"):
        raise HTTPException(status_code=403, detail="Not authorized")

    member = await db.get(TeamMember, member_id)
    if not member or member.team_id != team_id:
        raise HTTPException(status_code=404, detail="Member not found")

    # Can't change owner role
    if member.role == TeamRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot change owner role")

    member.role = role_data.role
    await db.commit()

    return {"message": "Role updated"}


@router.delete("/{team_id}/members/{member_id}")
async def remove_member(
    team_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the team."""
    if not await check_permission(db, team_id, current_user.id, "manage_team"):
        raise HTTPException(status_code=403, detail="Not authorized")

    member = await db.get(TeamMember, member_id)
    if not member or member.team_id != team_id:
        raise HTTPException(status_code=404, detail="Member not found")

    # Can't remove owner
    if member.role == TeamRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")

    await db.delete(member)
    await db.commit()

    return {"message": "Member removed"}


# Project access management
@router.post("/{team_id}/projects")
async def grant_project_access(
    team_id: UUID,
    access_data: ProjectAccessGrant,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grant team access to a project."""
    if not await check_permission(db, team_id, current_user.id, "manage_project"):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if access already exists
    result = await db.execute(
        select(ProjectTeamAccess).where(
            and_(
                ProjectTeamAccess.team_id == team_id,
                ProjectTeamAccess.project_id == access_data.project_id,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.can_edit = access_data.can_edit
        existing.can_comment = access_data.can_comment
        existing.can_export = access_data.can_export
    else:
        access = ProjectTeamAccess(
            team_id=team_id,
            project_id=access_data.project_id,
            can_edit=access_data.can_edit,
            can_comment=access_data.can_comment,
            can_export=access_data.can_export,
            granted_by_id=current_user.id,
        )
        db.add(access)

    await db.commit()
    return {"message": "Project access updated"}


@router.get("/{team_id}/projects")
async def list_team_projects(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List projects the team has access to."""
    member = await get_team_member(db, team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")

    result = await db.execute(
        select(ProjectTeamAccess).where(ProjectTeamAccess.team_id == team_id)
    )

    projects = []
    for access in result.scalars():
        projects.append({
            "project_id": str(access.project_id),
            "can_edit": access.can_edit,
            "can_comment": access.can_comment,
            "can_export": access.can_export,
            "granted_at": access.granted_at.isoformat() if access.granted_at else None,
        })

    return {"projects": projects}


@router.delete("/{team_id}/projects/{project_id}")
async def revoke_project_access(
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke team access to a project."""
    if not await check_permission(db, team_id, current_user.id, "manage_project"):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(ProjectTeamAccess).where(
            and_(
                ProjectTeamAccess.team_id == team_id,
                ProjectTeamAccess.project_id == project_id,
            )
        )
    )
    access = result.scalar_one_or_none()

    if not access:
        raise HTTPException(status_code=404, detail="Access not found")

    await db.delete(access)
    await db.commit()

    return {"message": "Access revoked"}
