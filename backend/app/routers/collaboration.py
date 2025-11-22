"""Collaboration API routes for comments, sharing, and notifications."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from app.models.user import User
from app.models.collaboration import (
    Comment, CommentType, CommentStatus,
    ProjectShare, SharePermission,
    ActivityLog, Notification
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])


# Schemas
class CommentCreate(BaseModel):
    content: str
    comment_type: str = "general"
    target_type: str
    target_id: UUID
    section_id: Optional[str] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    highlighted_text: Optional[str] = None
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


class ShareCreate(BaseModel):
    project_id: UUID
    shared_with_email: str
    permission: str = "view"
    message: Optional[str] = None


class CommentResponse(BaseModel):
    id: UUID
    content: str
    comment_type: str
    status: str
    author_id: UUID
    author_name: Optional[str] = None
    target_type: str
    target_id: UUID
    section_id: Optional[str] = None
    highlighted_text: Optional[str] = None
    parent_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    reply_count: int = 0

    class Config:
        from_attributes = True


# Comment endpoints
@router.post("/comments", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new comment."""
    comment = Comment(
        content=comment_data.content,
        comment_type=CommentType(comment_data.comment_type),
        author_id=current_user.id,
        target_type=comment_data.target_type,
        target_id=comment_data.target_id,
        section_id=comment_data.section_id,
        position_start=comment_data.position_start,
        position_end=comment_data.position_end,
        highlighted_text=comment_data.highlighted_text,
        parent_id=comment_data.parent_id,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action="commented",
        target_type=comment_data.target_type,
        target_id=comment_data.target_id,
    )
    db.add(activity)
    await db.commit()

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        comment_type=comment.comment_type.value,
        status=comment.status.value,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        target_type=comment.target_type,
        target_id=comment.target_id,
        section_id=comment.section_id,
        highlighted_text=comment.highlighted_text,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/comments/{target_type}/{target_id}")
async def get_comments(
    target_type: str,
    target_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all comments for a target."""
    result = await db.execute(
        select(Comment)
        .where(
            and_(
                Comment.target_type == target_type,
                Comment.target_id == target_id,
                Comment.parent_id.is_(None),  # Top-level comments only
            )
        )
        .order_by(Comment.created_at.desc())
    )

    comments = []
    for comment in result.scalars():
        # Get reply count
        reply_count_result = await db.scalar(
            select(func.count(Comment.id)).where(Comment.parent_id == comment.id)
        )

        comments.append({
            "id": str(comment.id),
            "content": comment.content,
            "comment_type": comment.comment_type.value,
            "status": comment.status.value,
            "author_id": str(comment.author_id),
            "section_id": comment.section_id,
            "highlighted_text": comment.highlighted_text,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
            "reply_count": reply_count_result or 0,
        })

    return {"comments": comments}


@router.get("/comments/{comment_id}/replies")
async def get_comment_replies(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get replies to a comment."""
    result = await db.execute(
        select(Comment)
        .where(Comment.parent_id == comment_id)
        .order_by(Comment.created_at.asc())
    )

    replies = []
    for comment in result.scalars():
        replies.append({
            "id": str(comment.id),
            "content": comment.content,
            "comment_type": comment.comment_type.value,
            "status": comment.status.value,
            "author_id": str(comment.author_id),
            "created_at": comment.created_at.isoformat(),
        })

    return {"replies": replies}


@router.patch("/comments/{comment_id}")
async def update_comment(
    comment_id: UUID,
    update_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a comment."""
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    if update_data.content is not None:
        comment.content = update_data.content

    if update_data.status is not None:
        comment.status = CommentStatus(update_data.status)
        if update_data.status == "resolved":
            comment.resolved_at = datetime.utcnow()
            comment.resolved_by_id = current_user.id

    await db.commit()
    await db.refresh(comment)

    return {"message": "Comment updated", "id": str(comment.id)}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a comment."""
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    await db.delete(comment)
    await db.commit()

    return {"message": "Comment deleted"}


# Sharing endpoints
@router.post("/share")
async def share_project(
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Share a project with another user."""
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == share_data.shared_with_email)
    )
    shared_with_user = result.scalar_one_or_none()

    if not shared_with_user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    if shared_with_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")

    # Check if already shared
    existing = await db.execute(
        select(ProjectShare).where(
            and_(
                ProjectShare.project_id == share_data.project_id,
                ProjectShare.shared_with_id == shared_with_user.id,
                ProjectShare.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project already shared with this user")

    share = ProjectShare(
        project_id=share_data.project_id,
        shared_with_id=shared_with_user.id,
        shared_by_id=current_user.id,
        permission=SharePermission(share_data.permission),
        message=share_data.message,
    )

    db.add(share)

    # Create notification
    notification = Notification(
        user_id=shared_with_user.id,
        title="Project Shared With You",
        message=f"{current_user.full_name} shared a project with you",
        notification_type="share",
        link_type="project",
        link_id=share_data.project_id,
    )
    db.add(notification)

    await db.commit()
    await db.refresh(share)

    return {"message": "Project shared successfully", "share_id": str(share.id)}


@router.get("/shared-with-me")
async def get_shared_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get projects shared with the current user."""
    result = await db.execute(
        select(ProjectShare)
        .where(
            and_(
                ProjectShare.shared_with_id == current_user.id,
                ProjectShare.is_active == True,
            )
        )
        .order_by(ProjectShare.created_at.desc())
    )

    shares = []
    for share in result.scalars():
        shares.append({
            "id": str(share.id),
            "project_id": str(share.project_id),
            "permission": share.permission.value,
            "shared_by_id": str(share.shared_by_id),
            "message": share.message,
            "created_at": share.created_at.isoformat(),
        })

    return {"shared_projects": shares}


@router.delete("/share/{share_id}")
async def revoke_share(
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a project share."""
    share = await db.get(ProjectShare, share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    if share.shared_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this share")

    share.is_active = False
    await db.commit()

    return {"message": "Share revoked"}


# Notification endpoints
@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user notifications."""
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)

    result = await db.execute(query)

    notifications = []
    for notification in result.scalars():
        notifications.append({
            "id": str(notification.id),
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "link_type": notification.link_type,
            "link_id": str(notification.link_id) if notification.link_id else None,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
        })

    return {"notifications": notifications}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()

    return {"message": "Notification marked as read"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False,
            )
        )
    )

    for notification in result.scalars():
        notification.is_read = True
        notification.read_at = datetime.utcnow()

    await db.commit()

    return {"message": "All notifications marked as read"}


# Activity log endpoints
@router.get("/activity/{project_id}")
async def get_project_activity(
    project_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get activity log for a project."""
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )

    activities = []
    for activity in result.scalars():
        activities.append({
            "id": str(activity.id),
            "user_id": str(activity.user_id),
            "action": activity.action,
            "action_details": activity.action_details,
            "target_type": activity.target_type,
            "target_id": str(activity.target_id),
            "target_name": activity.target_name,
            "created_at": activity.created_at.isoformat(),
        })

    return {"activities": activities}


# Add missing import
from sqlalchemy import func
