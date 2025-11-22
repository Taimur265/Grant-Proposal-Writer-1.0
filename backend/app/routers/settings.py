"""User settings and organization profile API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.settings import UserSettings, OrganizationProfile, SavedTemplate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


# Schemas
class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    email_notifications: Optional[bool] = None
    email_deadline_reminders: Optional[bool] = None
    email_comment_notifications: Optional[bool] = None
    email_workflow_updates: Optional[bool] = None
    deadline_reminder_days: Optional[List[int]] = None
    auto_save: Optional[bool] = None
    spell_check: Optional[bool] = None
    ai_suggestions_enabled: Optional[bool] = None
    ai_provider: Optional[str] = None
    default_grant_type: Optional[str] = None
    default_indirect_rate: Optional[str] = None


class OrganizationProfileUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    organization_type: Optional[str] = None
    ein: Optional[str] = None
    duns: Optional[str] = None
    sam_uei: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    executive_director: Optional[str] = None
    authorized_representative: Optional[str] = None
    mission_statement: Optional[str] = None
    year_founded: Optional[str] = None
    annual_budget: Optional[str] = None
    staff_count: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    geographic_service_area: Optional[List[str]] = None
    indirect_cost_rate: Optional[str] = None


class SavedTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: str = "proposal"
    grant_type: Optional[str] = None
    content: dict = {}
    sections: List[dict] = []
    is_public: bool = False


# User Settings endpoints
@router.get("/")
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user settings."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "theme": settings.theme,
        "language": settings.language,
        "timezone": settings.timezone,
        "date_format": settings.date_format,
        "email_notifications": settings.email_notifications,
        "email_deadline_reminders": settings.email_deadline_reminders,
        "email_comment_notifications": settings.email_comment_notifications,
        "email_workflow_updates": settings.email_workflow_updates,
        "deadline_reminder_days": settings.deadline_reminder_days,
        "auto_save": settings.auto_save,
        "spell_check": settings.spell_check,
        "show_word_count": settings.show_word_count,
        "ai_suggestions_enabled": settings.ai_suggestions_enabled,
        "ai_provider": settings.ai_provider,
        "default_grant_type": settings.default_grant_type,
        "default_indirect_rate": settings.default_indirect_rate,
    }


@router.patch("/")
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user settings."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    update_dict = settings_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)

    await db.commit()
    return {"message": "Settings updated"}


# Organization Profile endpoints
@router.get("/organization")
async def get_organization_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization profile."""
    result = await db.execute(
        select(OrganizationProfile).where(OrganizationProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return {"profile": None}

    return {
        "id": str(profile.id),
        "name": profile.name,
        "legal_name": profile.legal_name,
        "organization_type": profile.organization_type,
        "ein": profile.ein,
        "duns": profile.duns,
        "sam_uei": profile.sam_uei,
        "address": profile.address,
        "city": profile.city,
        "state": profile.state,
        "zip_code": profile.zip_code,
        "country": profile.country,
        "phone": profile.phone,
        "website": profile.website,
        "executive_director": profile.executive_director,
        "authorized_representative": profile.authorized_representative,
        "finance_contact": profile.finance_contact,
        "mission_statement": profile.mission_statement,
        "year_founded": profile.year_founded,
        "annual_budget": profile.annual_budget,
        "staff_count": profile.staff_count,
        "focus_areas": profile.focus_areas,
        "geographic_service_area": profile.geographic_service_area,
        "target_populations": profile.target_populations,
        "fiscal_year_end": profile.fiscal_year_end,
        "indirect_cost_rate": profile.indirect_cost_rate,
        "has_audit": profile.has_audit,
        "certifications": profile.certifications,
    }


@router.post("/organization")
async def create_organization_profile(
    profile_data: OrganizationProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update organization profile."""
    result = await db.execute(
        select(OrganizationProfile).where(OrganizationProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        # Update existing
        update_dict = profile_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)
    else:
        # Create new
        if not profile_data.name:
            raise HTTPException(status_code=400, detail="Organization name is required")

        profile = OrganizationProfile(
            user_id=current_user.id,
            **profile_data.dict(exclude_unset=True),
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return {"id": str(profile.id), "message": "Organization profile saved"}


# Saved Templates endpoints
@router.get("/templates")
async def list_saved_templates(
    template_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's saved templates."""
    stmt = select(SavedTemplate).where(SavedTemplate.user_id == current_user.id)

    if template_type:
        stmt = stmt.where(SavedTemplate.template_type == template_type)

    result = await db.execute(stmt.order_by(SavedTemplate.updated_at.desc()))

    templates = []
    for template in result.scalars():
        templates.append({
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "grant_type": template.grant_type,
            "use_count": template.use_count,
            "last_used_at": template.last_used_at.isoformat() if template.last_used_at else None,
            "updated_at": template.updated_at.isoformat(),
        })

    return {"templates": templates}


@router.post("/templates")
async def create_saved_template(
    template_data: SavedTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a new template."""
    template = SavedTemplate(
        user_id=current_user.id,
        name=template_data.name,
        description=template_data.description,
        template_type=template_data.template_type,
        grant_type=template_data.grant_type,
        content=template_data.content,
        sections=template_data.sections,
        is_public=template_data.is_public,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {"id": str(template.id), "name": template.name}


@router.get("/templates/{template_id}")
async def get_saved_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a saved template."""
    template = await db.get(SavedTemplate, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.user_id != current_user.id and not template.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "template_type": template.template_type,
        "grant_type": template.grant_type,
        "content": template.content,
        "sections": template.sections,
        "is_public": template.is_public,
    }


@router.delete("/templates/{template_id}")
async def delete_saved_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved template."""
    template = await db.get(SavedTemplate, template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(template)
    await db.commit()

    return {"message": "Template deleted"}
