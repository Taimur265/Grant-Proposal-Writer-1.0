"""Audit logging service."""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, AccessLog, SecurityEvent, AuditAction, ResourceType


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[UUID],
        user_email: Optional[str],
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: Optional[UUID] = None,
        resource_name: Optional[str] = None,
        action_description: Optional[str] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        changes: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        parent_resource_type: Optional[str] = None,
        parent_resource_id: Optional[UUID] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            action_description=action_description,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            parent_resource_type=parent_resource_type,
            parent_resource_id=parent_resource_id,
            old_value=old_value,
            new_value=new_value,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata=metadata,
            success=success,
            error_message=error_message,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def log_access(
        db: AsyncSession,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        access_type: str,
        ip_address: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> AccessLog:
        """Log resource access."""
        log = AccessLog(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            access_type=access_type,
            ip_address=ip_address,
            duration_seconds=duration_seconds,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        event_type: str,
        description: str,
        user_id: Optional[UUID] = None,
        severity: str = "info",
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
    ) -> SecurityEvent:
        """Log a security event."""
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    def compute_changes(old_value: Dict, new_value: Dict) -> Dict:
        """Compute the differences between old and new values."""
        changes = {
            "added": {},
            "removed": {},
            "modified": {},
        }

        old_keys = set(old_value.keys()) if old_value else set()
        new_keys = set(new_value.keys()) if new_value else set()

        # Added keys
        for key in new_keys - old_keys:
            changes["added"][key] = new_value[key]

        # Removed keys
        for key in old_keys - new_keys:
            changes["removed"][key] = old_value[key]

        # Modified keys
        for key in old_keys & new_keys:
            if old_value[key] != new_value[key]:
                changes["modified"][key] = {
                    "old": old_value[key],
                    "new": new_value[key],
                }

        return changes

    @staticmethod
    def action_description(action: AuditAction, resource_type: ResourceType, resource_name: Optional[str] = None) -> str:
        """Generate human-readable action description."""
        action_verbs = {
            AuditAction.CREATE: "created",
            AuditAction.READ: "viewed",
            AuditAction.UPDATE: "updated",
            AuditAction.DELETE: "deleted",
            AuditAction.LOGIN: "logged in",
            AuditAction.LOGOUT: "logged out",
            AuditAction.EXPORT: "exported",
            AuditAction.SHARE: "shared",
            AuditAction.SUBMIT: "submitted",
            AuditAction.APPROVE: "approved",
            AuditAction.REJECT: "rejected",
            AuditAction.UPLOAD: "uploaded",
            AuditAction.DOWNLOAD: "downloaded",
            AuditAction.GENERATE: "generated",
            AuditAction.INVITE: "invited user to",
            AuditAction.PERMISSION_CHANGE: "changed permissions for",
        }

        verb = action_verbs.get(action, action.value)
        resource = resource_type.value.replace("_", " ")

        if resource_name:
            return f"{verb} {resource}: {resource_name}"
        return f"{verb} {resource}"
