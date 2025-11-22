"""Narrative Builder and Boilerplate API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.narrative import (
    ProposalNarrative, NarrativeSection, SectionRevision, BoilerplateText, BudgetJustification,
    SectionType
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/narrative", tags=["Narrative Builder"])


class NarrativeCreate(BaseModel):
    title: str
    funder_name: Optional[str] = None
    max_pages: Optional[int] = None
    max_words: Optional[int] = None
    project_id: Optional[UUID] = None
    proposal_id: Optional[UUID] = None


class SectionCreate(BaseModel):
    narrative_id: UUID
    section_type: SectionType
    title: str
    content: Optional[str] = None
    max_words: Optional[int] = None
    is_required: bool = True
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class BoilerplateCreate(BaseModel):
    title: str
    category: str
    content: str
    short_version: Optional[str] = None
    medium_version: Optional[str] = None
    long_version: Optional[str] = None
    tags: Optional[List[str]] = None


class BudgetJustificationCreate(BaseModel):
    project_id: Optional[UUID] = None
    budget_category: str
    line_item: str
    amount: float
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    justification: str
    calculation_basis: Optional[str] = None
    match_amount: Optional[float] = None
    match_source: Optional[str] = None


# Narrative CRUD
@router.post("/")
async def create_narrative(
    data: NarrativeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a proposal narrative structure."""
    narrative = ProposalNarrative(user_id=current_user.id, **data.dict())
    db.add(narrative)
    await db.commit()
    await db.refresh(narrative)
    return {"id": str(narrative.id), "title": narrative.title}


@router.get("/")
async def list_narratives(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List proposal narratives."""
    stmt = select(ProposalNarrative).where(ProposalNarrative.user_id == current_user.id)
    if project_id:
        stmt = stmt.where(ProposalNarrative.project_id == project_id)

    result = await db.execute(stmt.order_by(ProposalNarrative.updated_at.desc()))

    return {
        "narratives": [
            {
                "id": str(n.id),
                "title": n.title,
                "funder_name": n.funder_name,
                "current_word_count": n.current_word_count,
                "max_words": n.max_words,
                "status": n.status,
                "version": n.version,
            }
            for n in result.scalars()
        ]
    }


@router.get("/{narrative_id}")
async def get_narrative(
    narrative_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get narrative with all sections."""
    narrative = await db.get(ProposalNarrative, narrative_id)
    if not narrative or narrative.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Narrative not found")

    sections_result = await db.execute(
        select(NarrativeSection)
        .where(NarrativeSection.narrative_id == narrative_id)
        .order_by(NarrativeSection.order_index)
    )

    return {
        "id": str(narrative.id),
        "title": narrative.title,
        "funder_name": narrative.funder_name,
        "max_pages": narrative.max_pages,
        "max_words": narrative.max_words,
        "current_word_count": narrative.current_word_count,
        "status": narrative.status,
        "version": narrative.version,
        "sections": [
            {
                "id": str(s.id),
                "section_type": s.section_type.value,
                "title": s.title,
                "content": s.content,
                "guidance_notes": s.guidance_notes,
                "max_words": s.max_words,
                "current_word_count": s.current_word_count,
                "is_required": s.is_required,
                "status": s.status,
                "assigned_to": s.assigned_to,
                "writing_tips": s.writing_tips,
                "key_points_to_include": s.key_points_to_include,
            }
            for s in sections_result.scalars()
        ],
    }


# Sections
@router.post("/sections")
async def create_section(
    data: SectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a section to a narrative."""
    section = NarrativeSection(**data.dict())
    db.add(section)
    await db.commit()
    return {"id": str(section.id)}


@router.patch("/sections/{section_id}")
async def update_section_content(
    section_id: UUID,
    content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update section content and save revision."""
    section = await db.get(NarrativeSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Save revision
    revision = SectionRevision(
        section_id=section_id,
        content=section.content or "",
        version=len([]) + 1,  # Get current revision count
        created_by=current_user.email
    )
    db.add(revision)

    # Update section
    section.content = content
    section.current_word_count = len(content.split())
    section.updated_at = datetime.utcnow()

    await db.commit()
    return {"message": "Section updated", "word_count": section.current_word_count}


# Boilerplate Library
@router.post("/boilerplate")
async def create_boilerplate(
    data: BoilerplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create boilerplate text."""
    boilerplate = BoilerplateText(
        user_id=current_user.id,
        word_count=len(data.content.split()),
        **data.dict()
    )
    db.add(boilerplate)
    await db.commit()
    return {"id": str(boilerplate.id)}


@router.get("/boilerplate")
async def list_boilerplate(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List boilerplate texts."""
    stmt = select(BoilerplateText).where(
        BoilerplateText.user_id == current_user.id,
        BoilerplateText.is_active == True
    )

    if category:
        stmt = stmt.where(BoilerplateText.category == category)
    if search:
        stmt = stmt.where(BoilerplateText.title.ilike(f"%{search}%"))

    result = await db.execute(stmt.order_by(BoilerplateText.use_count.desc()))

    return {
        "boilerplate": [
            {
                "id": str(b.id),
                "title": b.title,
                "category": b.category,
                "content": b.content[:200] + "..." if len(b.content) > 200 else b.content,
                "word_count": b.word_count,
                "use_count": b.use_count,
                "tags": b.tags,
            }
            for b in result.scalars()
        ]
    }


@router.get("/boilerplate/{boilerplate_id}")
async def get_boilerplate(
    boilerplate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get boilerplate text and track usage."""
    boilerplate = await db.get(BoilerplateText, boilerplate_id)
    if not boilerplate or boilerplate.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Boilerplate not found")

    # Track usage
    boilerplate.use_count += 1
    boilerplate.last_used = datetime.utcnow()
    await db.commit()

    return {
        "id": str(boilerplate.id),
        "title": boilerplate.title,
        "category": boilerplate.category,
        "content": boilerplate.content,
        "short_version": boilerplate.short_version,
        "medium_version": boilerplate.medium_version,
        "long_version": boilerplate.long_version,
        "word_count": boilerplate.word_count,
        "tags": boilerplate.tags,
    }


# Budget Justifications
@router.post("/budget-justification")
async def create_budget_justification(
    data: BudgetJustificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a budget justification."""
    justification = BudgetJustification(user_id=current_user.id, **data.dict())
    db.add(justification)
    await db.commit()
    return {"id": str(justification.id)}


@router.get("/budget-justification")
async def list_budget_justifications(
    project_id: Optional[UUID] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List budget justifications."""
    stmt = select(BudgetJustification).where(BudgetJustification.user_id == current_user.id)

    if project_id:
        stmt = stmt.where(BudgetJustification.project_id == project_id)
    if category:
        stmt = stmt.where(BudgetJustification.budget_category == category)

    result = await db.execute(stmt.order_by(BudgetJustification.budget_category))

    return {
        "justifications": [
            {
                "id": str(j.id),
                "budget_category": j.budget_category,
                "line_item": j.line_item,
                "amount": j.amount,
                "justification": j.justification,
                "match_amount": j.match_amount,
            }
            for j in result.scalars()
        ]
    }


@router.get("/section-types")
async def get_section_types():
    """Get available section types and boilerplate categories."""
    return {
        "section_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in SectionType
        ],
        "boilerplate_categories": [
            {"value": "organization", "label": "Organization Description"},
            {"value": "mission", "label": "Mission Statement"},
            {"value": "history", "label": "Organization History"},
            {"value": "capacity", "label": "Organizational Capacity"},
            {"value": "leadership", "label": "Leadership"},
            {"value": "financials", "label": "Financial Statements"},
            {"value": "programs", "label": "Program Descriptions"},
            {"value": "partnerships", "label": "Partnerships"},
            {"value": "evaluation", "label": "Evaluation Capacity"},
            {"value": "dei", "label": "DEI Statement"},
        ],
        "budget_categories": [
            {"value": "personnel", "label": "Personnel"},
            {"value": "fringe", "label": "Fringe Benefits"},
            {"value": "travel", "label": "Travel"},
            {"value": "equipment", "label": "Equipment"},
            {"value": "supplies", "label": "Supplies"},
            {"value": "contractual", "label": "Contractual"},
            {"value": "construction", "label": "Construction"},
            {"value": "other", "label": "Other Direct Costs"},
            {"value": "indirect", "label": "Indirect Costs"},
        ],
    }
