"""AI-powered proposal improvement API routes."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.proposal import Proposal
from app.routers.auth import get_current_user
from app.services.ai_improvement import AIImprovementService

router = APIRouter(prefix="/ai", tags=["AI Improvement"])


class TextAnalysisRequest(BaseModel):
    content: str
    sections: Optional[List[dict]] = None


class SectionTipsRequest(BaseModel):
    section_type: str


@router.post("/analyze")
async def analyze_proposal_text(
    request: TextAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze proposal text and get improvement suggestions."""
    analysis = AIImprovementService.analyze_proposal(
        content=request.content,
        sections=request.sections,
    )
    return {"analysis": analysis}


@router.get("/analyze/{proposal_id}")
async def analyze_stored_proposal(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a stored proposal."""
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if not proposal.content:
        raise HTTPException(status_code=400, detail="Proposal has no content")

    analysis = AIImprovementService.analyze_proposal(
        content=proposal.content,
        sections=None,
    )

    return {
        "proposal_id": str(proposal_id),
        "proposal_title": proposal.title,
        "analysis": analysis,
    }


@router.get("/templates/{grant_type}")
async def get_section_templates(
    grant_type: str,
    current_user: User = Depends(get_current_user),
):
    """Get recommended sections for a grant type."""
    templates = AIImprovementService.get_section_templates(grant_type)
    return {"grant_type": grant_type, "sections": templates}


@router.post("/tips")
async def get_writing_tips(
    request: SectionTipsRequest,
    current_user: User = Depends(get_current_user),
):
    """Get writing tips for a specific section type."""
    tips = AIImprovementService.generate_writing_tips(request.section_type)
    return {"section_type": request.section_type, "tips": tips}


@router.get("/best-practices")
async def get_best_practices(
    current_user: User = Depends(get_current_user),
):
    """Get all grant writing best practices."""
    return {"best_practices": AIImprovementService.BEST_PRACTICES}
