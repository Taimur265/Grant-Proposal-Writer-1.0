"""Project API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.document import Document, DocumentCategory
from app.models.proposal import Proposal
from app.models.user import User
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse, ProjectStats
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(
        **project_data.model_dump(),
        owner_id=current_user.id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[ProjectStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    # Base query
    query = select(Project).where(Project.owner_id == current_user.id)

    # Apply filters
    if status_filter:
        query = query.where(Project.status == status_filter)
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Apply pagination
    query = query.order_by(Project.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    # Get document and proposal counts for each project
    project_responses = []
    for project in projects:
        doc_count = (await db.execute(
            select(func.count()).where(Document.project_id == project.id)
        )).scalar()
        proposal_count = (await db.execute(
            select(func.count()).where(Proposal.project_id == project.id)
        )).scalar()

        project_dict = {
            **project.__dict__,
            "document_count": doc_count,
            "proposal_count": proposal_count,
        }
        project_responses.append(ProjectResponse(**project_dict))

    return ProjectListResponse(
        items=project_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get counts
    doc_count = (await db.execute(
        select(func.count()).where(Document.project_id == project.id)
    )).scalar()
    proposal_count = (await db.execute(
        select(func.count()).where(Proposal.project_id == project.id)
    )).scalar()

    return ProjectResponse(
        **project.__dict__,
        document_count=doc_count,
        proposal_count=proposal_count,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in project_update.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all associated data."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(project)


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get document counts by category
    total_docs = (await db.execute(
        select(func.count()).where(Document.project_id == project_id)
    )).scalar()

    guidelines_docs = (await db.execute(
        select(func.count()).where(
            Document.project_id == project_id,
            Document.category == DocumentCategory.GUIDELINES,
        )
    )).scalar()

    beneficiary_docs = (await db.execute(
        select(func.count()).where(
            Document.project_id == project_id,
            Document.category == DocumentCategory.BENEFICIARY,
        )
    )).scalar()

    # Get proposal count and latest status
    total_proposals = (await db.execute(
        select(func.count()).where(Proposal.project_id == project_id)
    )).scalar()

    latest_proposal = (await db.execute(
        select(Proposal)
        .where(Proposal.project_id == project_id)
        .order_by(Proposal.updated_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    return ProjectStats(
        total_documents=total_docs,
        guidelines_documents=guidelines_docs,
        beneficiary_documents=beneficiary_docs,
        total_proposals=total_proposals,
        latest_proposal_status=latest_proposal.status.value if latest_proposal else None,
    )
