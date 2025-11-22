"""Compliance checking API routes."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.document import Document
from app.services.compliance import ComplianceChecker
from app.routers.auth import get_current_user

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class QuickCheckRequest(BaseModel):
    content: str
    word_limit: Optional[int] = None
    page_limit: Optional[int] = None
    required_sections: list[str] = []


class ComplianceCheckRequest(BaseModel):
    proposal_id: Optional[UUID] = None
    proposal_content: Optional[str] = None
    guidelines_content: Optional[str] = None
    guidelines_document_id: Optional[UUID] = None
    budget_data: Optional[dict] = None
    organization_data: Optional[dict] = None


@router.post("/check")
async def check_compliance(
    request: ComplianceCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform comprehensive compliance check on a proposal."""
    proposal_content = request.proposal_content
    guidelines_content = request.guidelines_content

    # Get proposal content if ID provided
    if request.proposal_id:
        proposal = await db.get(Proposal, request.proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # Verify access
        project = await db.get(Project, proposal.project_id)
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        proposal_content = proposal.content

    # Get guidelines content if document ID provided
    if request.guidelines_document_id:
        document = await db.get(Document, request.guidelines_document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Guidelines document not found")

        guidelines_content = document.extracted_text or ""

    if not proposal_content:
        raise HTTPException(status_code=400, detail="Proposal content required")

    if not guidelines_content:
        raise HTTPException(status_code=400, detail="Guidelines content required")

    # Perform compliance check
    results = ComplianceChecker.check_compliance(
        proposal_content=proposal_content,
        guidelines_content=guidelines_content,
        budget_data=request.budget_data,
        organization_data=request.organization_data,
    )

    return {
        "compliance_results": results,
        "summary": {
            "overall_score": results["overall_score"],
            "passed_count": len(results["passed_checks"]),
            "failed_count": len(results["failed_checks"]),
            "warning_count": len(results["warnings"]),
            "is_compliant": results["overall_score"] >= 70 and len([
                c for c in results["failed_checks"]
                if c.get("severity") == "critical"
            ]) == 0,
        },
    }


@router.post("/quick-check")
async def quick_compliance_check(
    request: QuickCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """Perform quick compliance check with specific requirements."""
    requirements = {
        "word_limit": request.word_limit,
        "page_limit": request.page_limit,
        "required_sections": request.required_sections,
    }

    results = ComplianceChecker.quick_check(request.content, requirements)

    return {
        "compliant": results["compliant"],
        "word_count": results["word_count"],
        "issues": results["issues"],
    }


@router.get("/project/{project_id}")
async def check_project_compliance(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check compliance for all proposals in a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get all proposals for the project
    result = await db.execute(
        select(Proposal).where(Proposal.project_id == project_id)
    )
    proposals = result.scalars().all()

    # Get guidelines documents
    result = await db.execute(
        select(Document).where(
            Document.project_id == project_id,
            Document.category == "guidelines",
        )
    )
    guidelines_docs = result.scalars().all()

    # Combine guidelines text
    guidelines_content = "\n\n".join([
        doc.extracted_text or "" for doc in guidelines_docs
    ])

    if not guidelines_content:
        return {
            "error": "No guidelines documents found",
            "proposals": [],
        }

    # Check each proposal
    proposal_results = []
    for proposal in proposals:
        if not proposal.content:
            proposal_results.append({
                "proposal_id": str(proposal.id),
                "title": proposal.title,
                "status": "no_content",
                "compliance": None,
            })
            continue

        compliance = ComplianceChecker.check_compliance(
            proposal_content=proposal.content,
            guidelines_content=guidelines_content,
        )

        proposal_results.append({
            "proposal_id": str(proposal.id),
            "title": proposal.title,
            "status": "checked",
            "compliance": {
                "overall_score": compliance["overall_score"],
                "passed_count": len(compliance["passed_checks"]),
                "failed_count": len(compliance["failed_checks"]),
                "warning_count": len(compliance["warnings"]),
                "category_scores": {
                    cat_id: data["score"]
                    for cat_id, data in compliance["category_scores"].items()
                },
            },
        })

    return {
        "project_id": str(project_id),
        "proposals": proposal_results,
        "guidelines_document_count": len(guidelines_docs),
    }


@router.get("/requirements/{document_id}")
async def extract_requirements(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract requirements from a guidelines document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify access through project
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    requirements = ComplianceChecker._extract_requirements(document.extracted_text)

    return {
        "document_id": str(document_id),
        "document_name": document.original_filename,
        "requirements": requirements,
    }


@router.get("/categories")
async def get_compliance_categories():
    """Get all compliance check categories."""
    return {
        "categories": [
            {
                "id": cat_id,
                "name": cat_info["name"],
                "weight": cat_info["weight"],
                "checks": cat_info["checks"],
            }
            for cat_id, cat_info in ComplianceChecker.COMPLIANCE_CATEGORIES.items()
        ],
    }
