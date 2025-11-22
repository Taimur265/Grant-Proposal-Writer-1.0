"""Document schemas for API validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.document import DocumentType, DocumentCategory


class DocumentBase(BaseModel):
    """Base document schema."""
    document_type: DocumentType = DocumentType.OTHER
    category: DocumentCategory


class DocumentUpload(DocumentBase):
    """Schema for document upload metadata."""
    project_id: UUID
    description: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    document_type: Optional[DocumentType] = None
    category: Optional[DocumentCategory] = None
    summary: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_extension: str
    document_type: DocumentType
    category: DocumentCategory
    processing_status: str
    processing_error: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    project_id: UUID
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentContent(BaseModel):
    """Schema for document content response."""
    id: UUID
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    extracted_metadata: Optional[Dict[str, Any]] = None


class DocumentAnalysis(BaseModel):
    """Schema for document analysis results."""
    document_id: UUID
    word_count: int
    page_count: Optional[int] = None
    key_topics: List[str]
    requirements: List[str]
    deadlines: List[Dict[str, Any]]
    budget_info: Optional[Dict[str, Any]] = None
    eligibility_criteria: List[str]
    evaluation_criteria: List[str]


class BulkDocumentUpload(BaseModel):
    """Schema for bulk document upload."""
    project_id: UUID
    category: DocumentCategory
    document_types: Optional[List[DocumentType]] = None
