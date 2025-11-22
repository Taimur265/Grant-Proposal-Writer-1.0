"""Grant calendar and reminder models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class EventType(enum.Enum):
    DEADLINE = "deadline"
    MILESTONE = "milestone"
    MEETING = "meeting"
    REMINDER = "reminder"
    REVIEW = "review"
    SUBMISSION = "submission"
    REPORT_DUE = "report_due"
    SITE_VISIT = "site_visit"
    CUSTOM = "custom"


class ReminderFrequency(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class CalendarEvent(Base):
    """Calendar event model."""

    __tablename__ = "calendar_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    opportunity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_opportunities.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), default=EventType.CUSTOM)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=True)

    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Reminder(Base):
    """Reminder model for events and deadlines."""

    __tablename__ = "reminders"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    event_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reminder_offset_days: Mapped[int] = mapped_column(Integer, default=0)  # Days before event

    frequency: Mapped[ReminderFrequency] = mapped_column(Enum(ReminderFrequency), default=ReminderFrequency.ONCE)

    notify_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_in_app: Mapped[bool] = mapped_column(Boolean, default=True)

    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DeadlineTracker(Base):
    """Track important deadlines for grants."""

    __tablename__ = "deadline_trackers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    opportunity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("grant_opportunities.id", ondelete="SET NULL"), nullable=True)

    deadline_name: Mapped[str] = mapped_column(String(500))
    deadline_type: Mapped[str] = mapped_column(String(100))  # submission, loi, report, etc.
    deadline_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, submitted, missed, extended
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checklist: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    reminder_days: Mapped[List[int]] = mapped_column(JSON, default=[30, 14, 7, 3, 1])

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
