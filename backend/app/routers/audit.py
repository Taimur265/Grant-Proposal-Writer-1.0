"""Audit logging API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.database import get_db
from app.models.user import User
from app.models.audit import AuditLog, AccessLog, SecurityEvent, AuditAction, ResourceType
from app.routers.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
async def list_audit_logs(
    action: Optional[AuditAction] = None,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    success_only: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with filtering."""
    # Build query
    stmt = select(AuditLog)

    # Apply filters
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= end_date)
    if success_only:
        stmt = stmt.where(AuditLog.success == True)

    # Order and paginate
    stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

    result = await db.execute(stmt)

    logs = []
    for log in result.scalars():
        logs.append({
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "user_email": log.user_email,
            "action": log.action.value,
            "action_description": log.action_description,
            "resource_type": log.resource_type.value,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "resource_name": log.resource_name,
            "success": log.success,
            "error_message": log.error_message,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        })

    # Get total count
    count_stmt = select(func.count(AuditLog.id))
    if action:
        count_stmt = count_stmt.where(AuditLog.action == action)
    if resource_type:
        count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed audit log entry."""
    log = await db.get(AuditLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "user_email": log.user_email,
        "action": log.action.value,
        "action_description": log.action_description,
        "resource_type": log.resource_type.value,
        "resource_id": str(log.resource_id) if log.resource_id else None,
        "resource_name": log.resource_name,
        "parent_resource_type": log.parent_resource_type,
        "parent_resource_id": str(log.parent_resource_id) if log.parent_resource_id else None,
        "old_value": log.old_value,
        "new_value": log.new_value,
        "changes": log.changes,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "request_id": log.request_id,
        "metadata": log.metadata,
        "success": log.success,
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat(),
    }


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_audit_trail(
    resource_type: ResourceType,
    resource_id: UUID,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete audit trail for a resource."""
    result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id,
            )
        )
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )

    logs = []
    for log in result.scalars():
        logs.append({
            "id": str(log.id),
            "user_email": log.user_email,
            "action": log.action.value,
            "action_description": log.action_description,
            "changes": log.changes,
            "success": log.success,
            "created_at": log.created_at.isoformat(),
        })

    return {"resource_type": resource_type.value, "resource_id": str(resource_id), "audit_trail": logs}


@router.get("/user/{user_id}/activity")
async def get_user_activity(
    user_id: UUID,
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user activity summary."""
    start_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= start_date,
            )
        )
        .order_by(desc(AuditLog.created_at))
        .limit(100)
    )

    # Aggregate by action type
    action_counts = {}
    recent_activity = []

    for log in result.scalars():
        action_key = log.action.value
        action_counts[action_key] = action_counts.get(action_key, 0) + 1

        if len(recent_activity) < 20:
            recent_activity.append({
                "action": log.action.value,
                "resource_type": log.resource_type.value,
                "resource_name": log.resource_name,
                "created_at": log.created_at.isoformat(),
            })

    return {
        "user_id": str(user_id),
        "period_days": days,
        "action_summary": action_counts,
        "recent_activity": recent_activity,
    }


@router.get("/access-logs")
async def list_access_logs(
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List resource access logs."""
    stmt = select(AccessLog)

    if resource_type:
        stmt = stmt.where(AccessLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AccessLog.resource_id == resource_id)
    if user_id:
        stmt = stmt.where(AccessLog.user_id == user_id)

    stmt = stmt.order_by(desc(AccessLog.accessed_at)).limit(limit)

    result = await db.execute(stmt)

    logs = []
    for log in result.scalars():
        logs.append({
            "id": str(log.id),
            "user_id": str(log.user_id),
            "resource_type": log.resource_type.value,
            "resource_id": str(log.resource_id),
            "access_type": log.access_type,
            "duration_seconds": log.duration_seconds,
            "ip_address": log.ip_address,
            "accessed_at": log.accessed_at.isoformat(),
        })

    return {"access_logs": logs}


@router.get("/security-events")
async def list_security_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List security events."""
    stmt = select(SecurityEvent)

    if event_type:
        stmt = stmt.where(SecurityEvent.event_type == event_type)
    if severity:
        stmt = stmt.where(SecurityEvent.severity == severity)
    if user_id:
        stmt = stmt.where(SecurityEvent.user_id == user_id)
    if start_date:
        stmt = stmt.where(SecurityEvent.created_at >= start_date)

    stmt = stmt.order_by(desc(SecurityEvent.created_at)).limit(limit)

    result = await db.execute(stmt)

    events = []
    for event in result.scalars():
        events.append({
            "id": str(event.id),
            "user_id": str(event.user_id) if event.user_id else None,
            "event_type": event.event_type,
            "severity": event.severity,
            "description": event.description,
            "ip_address": event.ip_address,
            "location": event.location,
            "created_at": event.created_at.isoformat(),
        })

    return {"security_events": events}


@router.get("/summary")
async def get_audit_summary(
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit summary statistics."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Count by action
    action_counts = {}
    action_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.created_at >= start_date)
        .group_by(AuditLog.action)
    )
    for action, count in action_result:
        action_counts[action.value] = count

    # Count by resource type
    resource_counts = {}
    resource_result = await db.execute(
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(AuditLog.created_at >= start_date)
        .group_by(AuditLog.resource_type)
    )
    for resource_type, count in resource_result:
        resource_counts[resource_type.value] = count

    # Count failures
    failure_result = await db.execute(
        select(func.count(AuditLog.id))
        .where(and_(AuditLog.created_at >= start_date, AuditLog.success == False))
    )
    failure_count = failure_result.scalar()

    # Security events by severity
    security_counts = {}
    security_result = await db.execute(
        select(SecurityEvent.severity, func.count(SecurityEvent.id))
        .where(SecurityEvent.created_at >= start_date)
        .group_by(SecurityEvent.severity)
    )
    for severity, count in security_result:
        security_counts[severity] = count

    return {
        "period_days": days,
        "action_counts": action_counts,
        "resource_counts": resource_counts,
        "failure_count": failure_count,
        "security_events_by_severity": security_counts,
    }
