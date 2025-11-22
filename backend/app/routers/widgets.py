"""Dashboard widgets API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.widgets import DashboardWidget, DashboardLayout, WidgetType, DEFAULT_WIDGETS
from app.models.calendar import DeadlineTracker, CalendarEvent
from app.models.collaboration import ActivityLog
from app.routers.auth import get_current_user

router = APIRouter(prefix="/widgets", tags=["Widgets"])


# Schemas
class WidgetCreate(BaseModel):
    widget_type: WidgetType
    title: Optional[str] = None
    position_x: int = 0
    position_y: int = 0
    width: int = 1
    height: int = 1
    config: Optional[dict] = None


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[dict] = None
    is_visible: Optional[bool] = None
    is_collapsed: Optional[bool] = None


class LayoutUpdate(BaseModel):
    name: Optional[str] = None
    grid_columns: Optional[int] = None
    compact_mode: Optional[bool] = None
    widget_order: Optional[List[str]] = None


# Widget endpoints
@router.get("/")
async def list_widgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's dashboard widgets."""
    result = await db.execute(
        select(DashboardWidget)
        .where(DashboardWidget.user_id == current_user.id)
        .order_by(DashboardWidget.position_y, DashboardWidget.position_x)
    )

    widgets = []
    for widget in result.scalars():
        widgets.append({
            "id": str(widget.id),
            "widget_type": widget.widget_type.value,
            "title": widget.title,
            "position_x": widget.position_x,
            "position_y": widget.position_y,
            "width": widget.width,
            "height": widget.height,
            "config": widget.config,
            "is_visible": widget.is_visible,
            "is_collapsed": widget.is_collapsed,
        })

    # If no widgets, create defaults
    if not widgets:
        widgets = await create_default_widgets(current_user.id, db)

    return {"widgets": widgets}


async def create_default_widgets(user_id: UUID, db: AsyncSession) -> List[dict]:
    """Create default widgets for a user."""
    widgets = []
    for default in DEFAULT_WIDGETS:
        widget = DashboardWidget(
            user_id=user_id,
            widget_type=default["widget_type"],
            title=default["title"],
            position_x=default["position_x"],
            position_y=default["position_y"],
            width=default["width"],
            height=default["height"],
            config=default.get("config"),
        )
        db.add(widget)
        await db.flush()

        widgets.append({
            "id": str(widget.id),
            "widget_type": widget.widget_type.value,
            "title": widget.title,
            "position_x": widget.position_x,
            "position_y": widget.position_y,
            "width": widget.width,
            "height": widget.height,
            "config": widget.config,
            "is_visible": True,
            "is_collapsed": False,
        })

    await db.commit()
    return widgets


@router.post("/")
async def create_widget(
    widget_data: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new widget."""
    widget = DashboardWidget(
        user_id=current_user.id,
        widget_type=widget_data.widget_type,
        title=widget_data.title,
        position_x=widget_data.position_x,
        position_y=widget_data.position_y,
        width=widget_data.width,
        height=widget_data.height,
        config=widget_data.config,
    )
    db.add(widget)
    await db.commit()
    await db.refresh(widget)

    return {"id": str(widget.id), "widget_type": widget.widget_type.value}


@router.patch("/{widget_id}")
async def update_widget(
    widget_id: UUID,
    widget_data: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a widget."""
    widget = await db.get(DashboardWidget, widget_id)
    if not widget or widget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Widget not found")

    update_dict = widget_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(widget, key, value)

    await db.commit()
    return {"message": "Widget updated"}


@router.delete("/{widget_id}")
async def delete_widget(
    widget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a widget."""
    widget = await db.get(DashboardWidget, widget_id)
    if not widget or widget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Widget not found")

    await db.delete(widget)
    await db.commit()
    return {"message": "Widget deleted"}


@router.post("/reset")
async def reset_widgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset widgets to defaults."""
    # Delete existing widgets
    result = await db.execute(
        select(DashboardWidget).where(DashboardWidget.user_id == current_user.id)
    )
    for widget in result.scalars():
        await db.delete(widget)

    # Create defaults
    widgets = await create_default_widgets(current_user.id, db)
    return {"message": "Widgets reset", "widgets": widgets}


# Layout endpoints
@router.get("/layout")
async def get_layout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard layout configuration."""
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user.id)
    )
    layout = result.scalar_one_or_none()

    if not layout:
        layout = DashboardLayout(user_id=current_user.id)
        db.add(layout)
        await db.commit()
        await db.refresh(layout)

    return {
        "id": str(layout.id),
        "name": layout.name,
        "grid_columns": layout.grid_columns,
        "grid_row_height": layout.grid_row_height,
        "compact_mode": layout.compact_mode,
        "widget_order": layout.widget_order,
    }


@router.patch("/layout")
async def update_layout(
    layout_data: LayoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update dashboard layout."""
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user.id)
    )
    layout = result.scalar_one_or_none()

    if not layout:
        layout = DashboardLayout(user_id=current_user.id)
        db.add(layout)

    update_dict = layout_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(layout, key, value)

    await db.commit()
    return {"message": "Layout updated"}


# Widget data endpoints
@router.get("/data/{widget_type}")
async def get_widget_data(
    widget_type: WidgetType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get data for a specific widget type."""
    if widget_type == WidgetType.DEADLINES:
        return await get_deadlines_widget_data(current_user.id, db)
    elif widget_type == WidgetType.PROPOSALS_STATUS:
        return await get_proposals_status_data(current_user.id, db)
    elif widget_type == WidgetType.STATISTICS:
        return await get_statistics_data(current_user.id, db)
    elif widget_type == WidgetType.RECENT_ACTIVITY:
        return await get_recent_activity_data(current_user.id, db)
    else:
        return {"data": {}}


async def get_deadlines_widget_data(user_id: UUID, db: AsyncSession) -> dict:
    """Get upcoming deadlines data."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=30)

    result = await db.execute(
        select(DeadlineTracker)
        .where(
            DeadlineTracker.user_id == user_id,
            DeadlineTracker.deadline_date >= now,
            DeadlineTracker.deadline_date <= end_date,
            DeadlineTracker.status == "pending",
        )
        .order_by(DeadlineTracker.deadline_date)
        .limit(5)
    )

    deadlines = []
    for d in result.scalars():
        days_until = (d.deadline_date.replace(tzinfo=None) - now).days
        deadlines.append({
            "id": str(d.id),
            "name": d.deadline_name,
            "type": d.deadline_type,
            "date": d.deadline_date.isoformat(),
            "days_until": days_until,
            "priority": d.priority,
            "is_urgent": days_until <= 7,
        })

    return {"deadlines": deadlines, "total": len(deadlines)}


async def get_proposals_status_data(user_id: UUID, db: AsyncSession) -> dict:
    """Get proposal status breakdown."""
    result = await db.execute(
        select(Proposal.status, func.count(Proposal.id))
        .join(Project, Project.id == Proposal.project_id)
        .where(Project.owner_id == user_id)
        .group_by(Proposal.status)
    )

    status_counts = {}
    total = 0
    for status, count in result:
        status_counts[status] = count
        total += count

    return {
        "status_counts": status_counts,
        "total": total,
        "chart_data": [
            {"status": status, "count": count}
            for status, count in status_counts.items()
        ],
    }


async def get_statistics_data(user_id: UUID, db: AsyncSession) -> dict:
    """Get general statistics."""
    # Count projects
    projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == user_id)
    )
    projects_count = projects_result.scalar()

    # Count proposals
    proposals_result = await db.execute(
        select(func.count(Proposal.id))
        .join(Project, Project.id == Proposal.project_id)
        .where(Project.owner_id == user_id)
    )
    proposals_count = proposals_result.scalar()

    # Pending deadlines
    now = datetime.utcnow()
    deadlines_result = await db.execute(
        select(func.count(DeadlineTracker.id))
        .where(
            DeadlineTracker.user_id == user_id,
            DeadlineTracker.deadline_date >= now,
            DeadlineTracker.status == "pending",
        )
    )
    pending_deadlines = deadlines_result.scalar()

    return {
        "projects_count": projects_count,
        "proposals_count": proposals_count,
        "pending_deadlines": pending_deadlines,
    }


async def get_recent_activity_data(user_id: UUID, db: AsyncSession) -> dict:
    """Get recent activity."""
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
    )

    activities = []
    for activity in result.scalars():
        activities.append({
            "id": str(activity.id),
            "action": activity.action,
            "entity_type": activity.entity_type,
            "description": activity.description,
            "created_at": activity.created_at.isoformat(),
        })

    return {"activities": activities}


@router.get("/types")
async def list_widget_types(
    current_user: User = Depends(get_current_user),
):
    """List available widget types."""
    widget_info = {
        WidgetType.DEADLINES: {
            "name": "Upcoming Deadlines",
            "description": "Shows upcoming grant deadlines",
            "default_size": {"width": 4, "height": 2},
        },
        WidgetType.PROPOSALS_STATUS: {
            "name": "Proposal Status",
            "description": "Pie chart of proposal statuses",
            "default_size": {"width": 4, "height": 2},
        },
        WidgetType.RECENT_ACTIVITY: {
            "name": "Recent Activity",
            "description": "Recent actions and changes",
            "default_size": {"width": 6, "height": 2},
        },
        WidgetType.QUICK_ACTIONS: {
            "name": "Quick Actions",
            "description": "Common action buttons",
            "default_size": {"width": 4, "height": 2},
        },
        WidgetType.CALENDAR: {
            "name": "Calendar",
            "description": "Calendar view of events",
            "default_size": {"width": 6, "height": 3},
        },
        WidgetType.STATISTICS: {
            "name": "Statistics",
            "description": "Key metrics overview",
            "default_size": {"width": 4, "height": 2},
        },
        WidgetType.REMINDERS: {
            "name": "Reminders",
            "description": "Pending reminders list",
            "default_size": {"width": 4, "height": 2},
        },
    }

    return {
        "types": [
            {
                "type": wtype.value,
                **info,
            }
            for wtype, info in widget_info.items()
        ]
    }
