"""Letter generation API routes."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.services.letter_generator import LetterGenerator
from app.routers.auth import get_current_user

router = APIRouter(prefix="/letters", tags=["Letters"])


class LetterGenerateRequest(BaseModel):
    template_type: str
    data: dict
    project_id: Optional[UUID] = None


class LetterSaveRequest(BaseModel):
    template_type: str
    name: str
    content: str
    project_id: Optional[UUID] = None
    data: dict = {}


@router.get("/templates")
async def list_letter_templates(
    current_user: User = Depends(get_current_user),
):
    """List available letter templates."""
    return {"templates": LetterGenerator.list_templates()}


@router.get("/templates/{template_type}")
async def get_template_details(
    template_type: str,
    current_user: User = Depends(get_current_user),
):
    """Get details and fields for a specific template."""
    result = LetterGenerator.get_template_fields(template_type)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/generate")
async def generate_letter(
    request: LetterGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a letter from template."""
    result = LetterGenerator.generate_letter(
        template_type=request.template_type,
        data=request.data,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/generate/preview")
async def preview_letter(
    request: LetterGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """Preview a letter without saving."""
    result = LetterGenerator.generate_letter(
        template_type=request.template_type,
        data=request.data,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "preview": True,
        "content": result["content"],
        "template_name": result["template_name"],
    }


@router.get("/types")
async def get_letter_types(
    current_user: User = Depends(get_current_user),
):
    """Get categorized letter types."""
    return {
        "categories": [
            {
                "name": "Support Letters",
                "description": "Letters endorsing your organization or project",
                "types": [
                    {"type": "support_general", "name": "General Support Letter"},
                    {"type": "support_community", "name": "Community Support Letter"},
                    {"type": "support_government", "name": "Government Agency Support"},
                ],
            },
            {
                "name": "Commitment Letters",
                "description": "Letters confirming resource commitments",
                "types": [
                    {"type": "commitment_financial", "name": "Financial Commitment"},
                    {"type": "commitment_partnership", "name": "Partnership Commitment"},
                ],
            },
            {
                "name": "Formal Agreements",
                "description": "Formal documentation of partnerships",
                "types": [
                    {"type": "mou", "name": "Memorandum of Understanding"},
                ],
            },
        ],
    }


@router.get("/guidance/{letter_type}")
async def get_letter_guidance(
    letter_type: str,
    current_user: User = Depends(get_current_user),
):
    """Get guidance for writing effective letters."""
    guidance = {
        "support_general": {
            "title": "Tips for General Support Letters",
            "tips": [
                "Be specific about your relationship with the applicant organization",
                "Explain why you believe in the project's potential for success",
                "Mention any past collaborations or shared initiatives",
                "Keep the letter to one page if possible",
                "Use organizational letterhead",
                "Have an authorized representative sign the letter",
            ],
            "common_mistakes": [
                "Being too generic or vague",
                "Not mentioning specific project details",
                "Missing signature or contact information",
            ],
        },
        "commitment_financial": {
            "title": "Tips for Financial Commitment Letters",
            "tips": [
                "Clearly state the exact dollar amount committed",
                "Specify whether it's cash, in-kind, or both",
                "Describe how and when funds will be disbursed",
                "Note any conditions attached to the commitment",
                "Include authorized financial officer signature",
            ],
            "common_mistakes": [
                "Ambiguous commitment amounts",
                "Missing timeline for disbursement",
                "Unclear conditions or contingencies",
            ],
        },
        "mou": {
            "title": "Tips for MOUs",
            "tips": [
                "Clearly define roles and responsibilities for each party",
                "Specify the duration of the agreement",
                "Include modification and termination clauses",
                "Address confidentiality if needed",
                "Have legal review if involving significant commitments",
            ],
            "common_mistakes": [
                "Vague scope of collaboration",
                "Missing termination provisions",
                "Unclear resource commitments",
            ],
        },
    }

    if letter_type not in guidance:
        return {
            "title": "General Letter Writing Tips",
            "tips": [
                "Be clear and concise",
                "Use professional language",
                "Include contact information",
                "Sign on official letterhead",
            ],
        }

    return guidance[letter_type]
