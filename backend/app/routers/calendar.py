"""Grant calendar and reminders API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database import get_db
from app.models.user import User
from app.models.calendar import CalendarEvent, Reminder, DeadlineTracker, EventType, ReminderFrequency
from app.routers.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# Schemas
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: EventType = EventType.CUSTOM
    start_date: datetime
    end_date: Optional[datetime] = None
    all_day: bool = True
    project_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    location: Optional[str] = None
    url: Optional[str] = None
    color: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    url: Optional[str] = None
    color: Optional[str] = None
    is_completed: Optional[bool] = None


class ReminderCreate(BaseModel):
    title: str
    message: Optional[str] = None
    remind_at: datetime
    event_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    reminder_offset_days: int = 0
    frequency: ReminderFrequency = ReminderFrequency.ONCE
    notify_email: bool = True
    notify_in_app: bool = True


class DeadlineCreate(BaseModel):
    deadline_name: str
    deadline_type: str
    deadline_date: datetime
    project_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    priority: str = "medium"
    notes: Optional[str] = None
    checklist: Optional[List[dict]] = None
    reminder_days: List[int] = [30, 14, 7, 3, 1]


class DeadlineUpdate(BaseModel):
    deadline_name: Optional[str] = None
    deadline_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    checklist: Optional[List[dict]] = None
    submission_reference: Optional[str] = None


# Calendar Events
@router.post("/events")
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a calendar event."""
    event = CalendarEvent(
        user_id=current_user.id,
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        all_day=event_data.all_day,
        project_id=event_data.project_id,
        opportunity_id=event_data.opportunity_id,
        location=event_data.location,
        url=event_data.url,
        color=event_data.color,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "id": str(event.id),
        "title": event.title,
        "start_date": event.start_date.isoformat(),
    }


@router.get("/events")
async def list_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[EventType] = None,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List calendar events."""
    stmt = select(CalendarEvent).where(CalendarEvent.user_id == current_user.id)

    if start_date:
        stmt = stmt.where(CalendarEvent.start_date >= start_date)
    if end_date:
        stmt = stmt.where(CalendarEvent.start_date <= end_date)
    if event_type:
        stmt = stmt.where(CalendarEvent.event_type == event_type)
    if project_id:
        stmt = stmt.where(CalendarEvent.project_id == project_id)

    result = await db.execute(stmt.order_by(CalendarEvent.start_date))

    events = []
    for event in result.scalars():
        events.append({
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type.value,
            "start_date": event.start_date.isoformat(),
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "all_day": event.all_day,
            "project_id": str(event.project_id) if event.project_id else None,
            "location": event.location,
            "color": event.color,
            "is_completed": event.is_completed,
        })

    return {"events": events}


@router.get("/events/{event_id}")
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific event."""
    event = await db.get(CalendarEvent, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type.value,
        "start_date": event.start_date.isoformat(),
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "all_day": event.all_day,
        "project_id": str(event.project_id) if event.project_id else None,
        "opportunity_id": str(event.opportunity_id) if event.opportunity_id else None,
        "location": event.location,
        "url": event.url,
        "color": event.color,
        "is_completed": event.is_completed,
        "completed_at": event.completed_at.isoformat() if event.completed_at else None,
    }


@router.patch("/events/{event_id}")
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a calendar event."""
    event = await db.get(CalendarEvent, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Event not found")

    update_dict = event_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "is_completed" and value:
            event.completed_at = datetime.utcnow()
        setattr(event, key, value)

    await db.commit()
    return {"message": "Event updated"}


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a calendar event."""
    event = await db.get(CalendarEvent, event_id)
    if not event or event.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()
    return {"message": "Event deleted"}


# Reminders
@router.post("/reminders")
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a reminder."""
    reminder = Reminder(
        user_id=current_user.id,
        title=reminder_data.title,
        message=reminder_data.message,
        remind_at=reminder_data.remind_at,
        event_id=reminder_data.event_id,
        project_id=reminder_data.project_id,
        reminder_offset_days=reminder_data.reminder_offset_days,
        frequency=reminder_data.frequency,
        notify_email=reminder_data.notify_email,
        notify_in_app=reminder_data.notify_in_app,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    return {"id": str(reminder.id), "remind_at": reminder.remind_at.isoformat()}


@router.get("/reminders")
async def list_reminders(
    include_dismissed: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List reminders."""
    stmt = select(Reminder).where(Reminder.user_id == current_user.id)

    if not include_dismissed:
        stmt = stmt.where(Reminder.is_dismissed == False)

    result = await db.execute(stmt.order_by(Reminder.remind_at))

    reminders = []
    for reminder in result.scalars():
        reminders.append({
            "id": str(reminder.id),
            "title": reminder.title,
            "message": reminder.message,
            "remind_at": reminder.remind_at.isoformat(),
            "event_id": str(reminder.event_id) if reminder.event_id else None,
            "project_id": str(reminder.project_id) if reminder.project_id else None,
            "is_sent": reminder.is_sent,
            "is_dismissed": reminder.is_dismissed,
        })

    return {"reminders": reminders}


@router.get("/reminders/upcoming")
async def get_upcoming_reminders(
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming reminders within specified days."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    result = await db.execute(
        select(Reminder).where(
            and_(
                Reminder.user_id == current_user.id,
                Reminder.remind_at >= now,
                Reminder.remind_at <= end_date,
                Reminder.is_dismissed == False,
            )
        ).order_by(Reminder.remind_at)
    )

    reminders = []
    for reminder in result.scalars():
        reminders.append({
            "id": str(reminder.id),
            "title": reminder.title,
            "message": reminder.message,
            "remind_at": reminder.remind_at.isoformat(),
            "days_until": (reminder.remind_at - now).days,
        })

    return {"reminders": reminders}


@router.post("/reminders/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a reminder."""
    reminder = await db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.is_dismissed = True
    reminder.dismissed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Reminder dismissed"}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a reminder."""
    reminder = await db.get(Reminder, reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.delete(reminder)
    await db.commit()
    return {"message": "Reminder deleted"}


# Deadline Tracker
@router.post("/deadlines")
async def create_deadline(
    deadline_data: DeadlineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a deadline tracker."""
    deadline = DeadlineTracker(
        user_id=current_user.id,
        deadline_name=deadline_data.deadline_name,
        deadline_type=deadline_data.deadline_type,
        deadline_date=deadline_data.deadline_date,
        project_id=deadline_data.project_id,
        opportunity_id=deadline_data.opportunity_id,
        priority=deadline_data.priority,
        notes=deadline_data.notes,
        checklist=deadline_data.checklist,
        reminder_days=deadline_data.reminder_days,
    )
    db.add(deadline)
    await db.commit()
    await db.refresh(deadline)

    # Create reminders for this deadline
    for days_before in deadline_data.reminder_days:
        remind_at = deadline_data.deadline_date - timedelta(days=days_before)
        if remind_at > datetime.utcnow():
            reminder = Reminder(
                user_id=current_user.id,
                title=f"Deadline: {deadline_data.deadline_name}",
                message=f"{days_before} days until deadline",
                remind_at=remind_at,
                project_id=deadline_data.project_id,
                reminder_offset_days=days_before,
            )
            db.add(reminder)

    await db.commit()

    return {"id": str(deadline.id), "deadline_date": deadline.deadline_date.isoformat()}


@router.get("/deadlines")
async def list_deadlines(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[UUID] = None,
    days_ahead: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List deadline trackers."""
    stmt = select(DeadlineTracker).where(DeadlineTracker.user_id == current_user.id)

    if status:
        stmt = stmt.where(DeadlineTracker.status == status)
    if priority:
        stmt = stmt.where(DeadlineTracker.priority == priority)
    if project_id:
        stmt = stmt.where(DeadlineTracker.project_id == project_id)
    if days_ahead:
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        stmt = stmt.where(DeadlineTracker.deadline_date <= end_date)

    result = await db.execute(stmt.order_by(DeadlineTracker.deadline_date))

    deadlines = []
    now = datetime.utcnow()
    for deadline in result.scalars():
        days_until = (deadline.deadline_date.replace(tzinfo=None) - now).days if deadline.deadline_date else None
        deadlines.append({
            "id": str(deadline.id),
            "deadline_name": deadline.deadline_name,
            "deadline_type": deadline.deadline_type,
            "deadline_date": deadline.deadline_date.isoformat(),
            "days_until": days_until,
            "status": deadline.status,
            "priority": deadline.priority,
            "project_id": str(deadline.project_id) if deadline.project_id else None,
            "notes": deadline.notes,
            "checklist": deadline.checklist,
        })

    return {"deadlines": deadlines}


@router.get("/deadlines/upcoming")
async def get_upcoming_deadlines(
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming deadlines."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    result = await db.execute(
        select(DeadlineTracker).where(
            and_(
                DeadlineTracker.user_id == current_user.id,
                DeadlineTracker.deadline_date >= now,
                DeadlineTracker.deadline_date <= end_date,
                DeadlineTracker.status == "pending",
            )
        ).order_by(DeadlineTracker.deadline_date)
    )

    deadlines = []
    for deadline in result.scalars():
        days_until = (deadline.deadline_date.replace(tzinfo=None) - now).days
        deadlines.append({
            "id": str(deadline.id),
            "deadline_name": deadline.deadline_name,
            "deadline_type": deadline.deadline_type,
            "deadline_date": deadline.deadline_date.isoformat(),
            "days_until": days_until,
            "priority": deadline.priority,
            "is_urgent": days_until <= 7,
            "is_critical": days_until <= 3,
        })

    return {"deadlines": deadlines, "total": len(deadlines)}


@router.patch("/deadlines/{deadline_id}")
async def update_deadline(
    deadline_id: UUID,
    deadline_data: DeadlineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a deadline."""
    deadline = await db.get(DeadlineTracker, deadline_id)
    if not deadline or deadline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Deadline not found")

    update_dict = deadline_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "status" and value == "submitted":
            deadline.submitted_at = datetime.utcnow()
        setattr(deadline, key, value)

    await db.commit()
    return {"message": "Deadline updated"}


@router.post("/deadlines/{deadline_id}/submit")
async def mark_deadline_submitted(
    deadline_id: UUID,
    submission_reference: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a deadline as submitted."""
    deadline = await db.get(DeadlineTracker, deadline_id)
    if not deadline or deadline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Deadline not found")

    deadline.status = "submitted"
    deadline.submitted_at = datetime.utcnow()
    if submission_reference:
        deadline.submission_reference = submission_reference

    await db.commit()
    return {"message": "Deadline marked as submitted"}


@router.delete("/deadlines/{deadline_id}")
async def delete_deadline(
    deadline_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a deadline."""
    deadline = await db.get(DeadlineTracker, deadline_id)
    if not deadline or deadline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Deadline not found")

    await db.delete(deadline)
    await db.commit()
    return {"message": "Deadline deleted"}


# Calendar Overview
@router.get("/overview")
async def get_calendar_overview(
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar overview with events and deadlines."""
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    # Get events
    events_result = await db.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == current_user.id,
                CalendarEvent.start_date >= now,
                CalendarEvent.start_date <= end_date,
            )
        ).order_by(CalendarEvent.start_date)
    )

    # Get deadlines
    deadlines_result = await db.execute(
        select(DeadlineTracker).where(
            and_(
                DeadlineTracker.user_id == current_user.id,
                DeadlineTracker.deadline_date >= now,
                DeadlineTracker.deadline_date <= end_date,
                DeadlineTracker.status == "pending",
            )
        ).order_by(DeadlineTracker.deadline_date)
    )

    # Get upcoming reminders
    reminders_result = await db.execute(
        select(Reminder).where(
            and_(
                Reminder.user_id == current_user.id,
                Reminder.remind_at >= now,
                Reminder.remind_at <= end_date,
                Reminder.is_dismissed == False,
            )
        ).order_by(Reminder.remind_at)
    )

    events = [
        {
            "id": str(e.id),
            "type": "event",
            "title": e.title,
            "date": e.start_date.isoformat(),
            "event_type": e.event_type.value,
            "color": e.color,
        }
        for e in events_result.scalars()
    ]

    deadlines = [
        {
            "id": str(d.id),
            "type": "deadline",
            "title": d.deadline_name,
            "date": d.deadline_date.isoformat(),
            "priority": d.priority,
            "days_until": (d.deadline_date.replace(tzinfo=None) - now).days,
        }
        for d in deadlines_result.scalars()
    ]

    reminders = [
        {
            "id": str(r.id),
            "type": "reminder",
            "title": r.title,
            "date": r.remind_at.isoformat(),
        }
        for r in reminders_result.scalars()
    ]

    return {
        "events": events,
        "deadlines": deadlines,
        "reminders": reminders,
        "summary": {
            "total_events": len(events),
            "total_deadlines": len(deadlines),
            "total_reminders": len(reminders),
            "urgent_deadlines": sum(1 for d in deadlines if d["days_until"] <= 7),
        },
    }
