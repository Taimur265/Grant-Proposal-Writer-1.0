"""Dashboard widgets models."""

import enum
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class WidgetType(enum.Enum):
    DEADLINES = "deadlines"
    PROPOSALS_STATUS = "proposals_status"
    RECENT_ACTIVITY = "recent_activity"
    QUICK_ACTIONS = "quick_actions"
    CALENDAR = "calendar"
    STATISTICS = "statistics"
    FUNDERS = "funders"
    TEAM_ACTIVITY = "team_activity"
    COMPLIANCE = "compliance"
    BUDGET_OVERVIEW = "budget_overview"
    OPPORTUNITIES = "opportunities"
    REMINDERS = "reminders"
    CUSTOM = "custom"


class DashboardWidget(Base):
    """User dashboard widget configuration."""

    __tablename__ = "dashboard_widgets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    widget_type: Mapped[WidgetType] = mapped_column(Enum(WidgetType))
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Layout
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, default=1)  # Grid units
    height: Mapped[int] = mapped_column(Integer, default=1)  # Grid units

    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    is_collapsed: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Seconds

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class DashboardLayout(Base):
    """User dashboard layout configuration."""

    __tablename__ = "dashboard_layouts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    name: Mapped[str] = mapped_column(String(100), default="Default")
    grid_columns: Mapped[int] = mapped_column(Integer, default=12)
    grid_row_height: Mapped[int] = mapped_column(Integer, default=100)

    theme: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    compact_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    widget_order: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of widget IDs

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# Default widget configurations
DEFAULT_WIDGETS = [
    {
        "widget_type": WidgetType.DEADLINES,
        "title": "Upcoming Deadlines",
        "position_x": 0,
        "position_y": 0,
        "width": 4,
        "height": 2,
        "config": {"days_ahead": 30, "max_items": 5},
    },
    {
        "widget_type": WidgetType.PROPOSALS_STATUS,
        "title": "Proposal Status",
        "position_x": 4,
        "position_y": 0,
        "width": 4,
        "height": 2,
        "config": {"show_chart": True},
    },
    {
        "widget_type": WidgetType.QUICK_ACTIONS,
        "title": "Quick Actions",
        "position_x": 8,
        "position_y": 0,
        "width": 4,
        "height": 2,
        "config": {},
    },
    {
        "widget_type": WidgetType.RECENT_ACTIVITY,
        "title": "Recent Activity",
        "position_x": 0,
        "position_y": 2,
        "width": 6,
        "height": 2,
        "config": {"max_items": 10},
    },
    {
        "widget_type": WidgetType.CALENDAR,
        "title": "Calendar",
        "position_x": 6,
        "position_y": 2,
        "width": 6,
        "height": 2,
        "config": {"view": "week"},
    },
]
