"""Export API routes for proposals and reports."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.proposal import Proposal
from app.routers.auth import get_current_user
from app.services.export import ExportService
from app.services.budget import BudgetService

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/proposals/{proposal_id}/markdown")
async def export_proposal_markdown(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export proposal as Markdown."""
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal_dict = {
        "title": proposal.title,
        "content": proposal.content,
        "status": proposal.status.value,
        "word_count": proposal.word_count,
        "compliance_score": proposal.compliance_score,
        "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
    }

    markdown = ExportService.export_proposal_to_markdown(proposal_dict)

    return StreamingResponse(
        io.BytesIO(markdown.encode('utf-8')),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={proposal.title}.md"},
    )


@router.get("/proposals/{proposal_id}/html")
async def export_proposal_html(
    proposal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export proposal as HTML."""
    proposal = await db.get(Proposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal_dict = {
        "title": proposal.title,
        "content": proposal.content,
        "status": proposal.status.value,
        "word_count": proposal.word_count,
        "compliance_score": proposal.compliance_score,
        "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
    }

    html = ExportService.export_proposal_to_html(proposal_dict)

    return StreamingResponse(
        io.BytesIO(html.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={proposal.title}.html"},
    )


@router.get("/projects/{project_id}/report")
async def get_project_report(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate comprehensive project report."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get documents
    docs_result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )
    documents = []
    for doc in docs_result.scalars():
        documents.append({
            "original_filename": doc.original_filename,
            "category": doc.category.value,
            "document_type": doc.document_type.value,
            "processing_status": doc.processing_status,
            "file_size": doc.file_size,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })

    # Get proposals
    props_result = await db.execute(
        select(Proposal).where(Proposal.project_id == project_id)
    )
    proposals = []
    for prop in props_result.scalars():
        proposals.append({
            "title": prop.title,
            "status": prop.status.value,
            "word_count": prop.word_count,
            "compliance_score": prop.compliance_score,
            "created_at": prop.created_at.isoformat() if prop.created_at else None,
        })

    # Generate report
    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "grant_type": project.grant_type,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }

    report = ExportService.generate_project_report(project_dict, documents, proposals)
    return report


@router.get("/projects/{project_id}/report/json")
async def export_project_report_json(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export project report as JSON file."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get documents and proposals (same as above)
    docs_result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )
    documents = [{"original_filename": d.original_filename, "category": d.category.value,
                  "document_type": d.document_type.value, "processing_status": d.processing_status,
                  "file_size": d.file_size, "created_at": d.created_at.isoformat() if d.created_at else None}
                 for d in docs_result.scalars()]

    props_result = await db.execute(
        select(Proposal).where(Proposal.project_id == project_id)
    )
    proposals = [{"title": p.title, "status": p.status.value, "word_count": p.word_count,
                  "compliance_score": p.compliance_score,
                  "created_at": p.created_at.isoformat() if p.created_at else None}
                 for p in props_result.scalars()]

    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "grant_type": project.grant_type,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }

    report = ExportService.generate_project_report(project_dict, documents, proposals)
    json_content = ExportService.export_report_to_json(report)

    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={project.name}_report.json"},
    )


@router.get("/projects/{project_id}/documents/csv")
async def export_documents_csv(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export project documents list as CSV."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    docs_result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )
    documents = [{"original_filename": d.original_filename, "category": d.category.value,
                  "document_type": d.document_type.value, "processing_status": d.processing_status,
                  "file_size": d.file_size, "created_at": d.created_at.isoformat() if d.created_at else None}
                 for d in docs_result.scalars()]

    csv_content = ExportService.export_documents_list_to_csv(documents)

    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={project.name}_documents.csv"},
    )
