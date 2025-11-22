"""Template API routes."""

from typing import List, Optional
from fastapi import APIRouter, Query

from app.services.templates import TemplateService

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/")
async def list_templates():
    """List all available proposal templates."""
    return {
        "templates": TemplateService.get_template_names(),
    }


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template with all sections."""
    template = TemplateService.get_template(template_id)
    return {
        "id": template_id,
        **template,
    }


@router.get("/{template_id}/sections")
async def get_template_sections(
    template_id: str,
    include_sections: Optional[List[str]] = Query(None),
    max_words: Optional[int] = None,
):
    """Get sections for a template with optional customization."""
    sections = TemplateService.customize_template(
        template_id,
        custom_sections=include_sections,
        max_words=max_words,
    )
    return {
        "template_id": template_id,
        "sections": sections,
    }
