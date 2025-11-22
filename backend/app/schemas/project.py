"""Project schemas for API validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    grant_type: Optional[str] = None
    funding_agency: Optional[str] = None
    deadline: Optional[datetime] = None
    target_amount: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    grant_type: Optional[str] = None
    funding_agency: Optional[str] = None
    deadline: Optional[datetime] = None
    target_amount: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID
    status: ProjectStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
    proposal_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for paginated project list."""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectStats(BaseModel):
    """Schema for project statistics."""
    total_documents: int
    guidelines_documents: int
    beneficiary_documents: int
    total_proposals: int
    latest_proposal_status: Optional[str] = None
