"""Document model for storing uploaded files."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DocumentType(str, enum.Enum):
    """Document type enumeration for categorizing uploads."""
    # Guidelines Section
    GUIDELINES = "guidelines"
    TERMS_CONDITIONS = "terms_conditions"
    TOR = "tor"  # Terms of Reference
    RFP = "rfp"  # Request for Proposal
    ELIGIBILITY = "eligibility"
    EVALUATION_CRITERIA = "evaluation_criteria"
    BUDGET_TEMPLATE = "budget_template"

    # Beneficiary Section
    ORGANIZATION_PROFILE = "organization_profile"
    REGISTRATION_DOCS = "registration_docs"
    FINANCIAL_STATEMENTS = "financial_statements"
    PROJECT_DESCRIPTION = "project_description"
    BENEFICIARY_DATA = "beneficiary_data"
    IMPACT_ASSESSMENT = "impact_assessment"
    TEAM_CVS = "team_cvs"
    PAST_PERFORMANCE = "past_performance"
    LETTERS_OF_SUPPORT = "letters_of_support"

    # Other
    OTHER = "other"


class DocumentCategory(str, enum.Enum):
    """Main category for documents."""
    GUIDELINES = "guidelines"  # Guidelines, T&C, TORs section
    BENEFICIARY = "beneficiary"  # Beneficiary details section
    GENERATED = "generated"  # AI-generated content
    REFERENCE = "reference"  # Reference materials


class Document(Base):
    """Document model for storing uploaded files and extracted content."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(20), nullable=False)

    # Document classification
    document_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    category = Column(Enum(DocumentCategory), nullable=False)

    # Extracted content
    extracted_text = Column(Text, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)  # Structured data from document
    summary = Column(Text, nullable=True)  # AI-generated summary
    key_points = Column(JSON, nullable=True)  # Extracted key points

    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)

    # Foreign Keys
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Document {self.original_filename}>"
