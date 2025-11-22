"""User settings and preferences models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class UserSettings(Base):
    """User settings and preferences."""

    __tablename__ = "user_settings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Display preferences
    theme = Column(String(20), default="light")  # 'light', 'dark', 'system'
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="MM/DD/YYYY")

    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    email_deadline_reminders = Column(Boolean, default=True)
    email_comment_notifications = Column(Boolean, default=True)
    email_workflow_updates = Column(Boolean, default=True)
    deadline_reminder_days = Column(JSON, default=[7, 3, 1])  # Days before deadline

    # Editor preferences
    default_font_size = Column(String(10), default="14px")
    auto_save = Column(Boolean, default=True)
    auto_save_interval = Column(String(10), default="30s")
    spell_check = Column(Boolean, default=True)
    show_word_count = Column(Boolean, default=True)

    # AI preferences
    ai_suggestions_enabled = Column(Boolean, default=True)
    ai_provider = Column(String(50), default="openai")  # 'openai', 'anthropic'
    ai_model = Column(String(50), default="gpt-4")

    # Default project settings
    default_grant_type = Column(String(50), default="federal")
    default_indirect_rate = Column(String(10), default="0.54")

    # Custom settings
    custom_settings = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="settings")


class OrganizationProfile(Base):
    """Organization profile for grant applications."""

    __tablename__ = "organization_profiles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    organization_type = Column(String(100), nullable=True)
    ein = Column(String(20), nullable=True)  # Tax ID
    duns = Column(String(20), nullable=True)  # DUNS number
    sam_uei = Column(String(20), nullable=True)  # SAM.gov UEI

    # Contact info
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), default="United States")
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    # Leadership
    executive_director = Column(String(255), nullable=True)
    authorized_representative = Column(String(255), nullable=True)
    finance_contact = Column(String(255), nullable=True)

    # Organization details
    mission_statement = Column(Text, nullable=True)
    year_founded = Column(String(4), nullable=True)
    annual_budget = Column(String(50), nullable=True)
    staff_count = Column(String(20), nullable=True)

    # Grant-related
    focus_areas = Column(JSON, default=[])
    geographic_service_area = Column(JSON, default=[])
    target_populations = Column(JSON, default=[])

    # Financial
    fiscal_year_end = Column(String(10), nullable=True)
    indirect_cost_rate = Column(String(10), nullable=True)
    has_audit = Column(Boolean, default=False)

    # Certifications
    certifications = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="organization_profiles")


class SavedTemplate(Base):
    """User-saved proposal templates."""

    __tablename__ = "saved_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), default="proposal")  # 'proposal', 'section', 'budget'
    grant_type = Column(String(50), nullable=True)

    # Content
    content = Column(JSON, default={})
    sections = Column(JSON, default=[])

    # Usage
    use_count = Column(String(10), default="0")
    last_used_at = Column(DateTime, nullable=True)

    # Sharing
    is_public = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="saved_templates")
