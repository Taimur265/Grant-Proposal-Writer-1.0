"""Proposal schemas for API validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.proposal import ProposalStatus


class ProposalSectionBase(BaseModel):
    """Base proposal section schema."""
    section_name: str
    section_order: int
    content: Optional[str] = None
    max_words: Optional[int] = None
    is_required: bool = True


class ProposalSectionCreate(ProposalSectionBase):
    """Schema for creating a proposal section."""
    pass


class ProposalSectionUpdate(BaseModel):
    """Schema for updating a proposal section."""
    content: Optional[str] = None
    is_complete: Optional[bool] = None


class ProposalSectionResponse(ProposalSectionBase):
    """Schema for proposal section response."""
    id: UUID
    word_count: Optional[int] = None
    is_complete: bool
    ai_suggestions: Optional[List[str]] = None
    compliance_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProposalBase(BaseModel):
    """Base proposal schema."""
    title: str = Field(..., min_length=1, max_length=500)


class ProposalCreate(ProposalBase):
    """Schema for creating a new proposal."""
    project_id: UUID


class ProposalUpdate(BaseModel):
    """Schema for updating a proposal."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[ProposalStatus] = None
    executive_summary: Optional[str] = None


class ProposalResponse(ProposalBase):
    """Schema for proposal response."""
    id: UUID
    version: int
    status: ProposalStatus
    executive_summary: Optional[str] = None
    word_count: Optional[int] = None
    compliance_score: Optional[float] = None
    ai_model_used: Optional[str] = None
    project_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    sections: List[ProposalSectionResponse] = []

    class Config:
        from_attributes = True


class ProposalListResponse(BaseModel):
    """Schema for paginated proposal list."""
    items: List[ProposalResponse]
    total: int
    page: int
    page_size: int


class ProposalGenerate(BaseModel):
    """Schema for proposal generation request."""
    project_id: UUID
    title: Optional[str] = None
    ai_provider: Optional[str] = None  # "openai" or "anthropic"
    model: Optional[str] = None
    tone: Optional[str] = "professional"  # professional, academic, conversational
    focus_areas: Optional[List[str]] = None
    custom_instructions: Optional[str] = None
    include_sections: Optional[List[str]] = None
    max_words_per_section: Optional[int] = None


class ProposalExport(BaseModel):
    """Schema for proposal export request."""
    format: str = Field(..., pattern="^(docx|pdf|txt|html|md)$")
    include_metadata: bool = True
    include_comments: bool = False
    template_id: Optional[UUID] = None


class ProposalFeedbackCreate(BaseModel):
    """Schema for creating proposal feedback."""
    section_id: Optional[UUID] = None
    feedback_type: str = Field(..., pattern="^(comment|suggestion|approval|rejection)$")
    content: str


class ProposalFeedbackResponse(BaseModel):
    """Schema for proposal feedback response."""
    id: UUID
    proposal_id: UUID
    section_id: Optional[UUID] = None
    feedback_type: str
    content: str
    is_resolved: bool
    author_id: UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceCheck(BaseModel):
    """Schema for compliance check results."""
    overall_score: float
    section_scores: Dict[str, float]
    missing_requirements: List[str]
    suggestions: List[str]
    word_count_status: Dict[str, Dict[str, Any]]
