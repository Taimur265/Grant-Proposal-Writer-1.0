"""Document analysis API routes."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.routers.auth import get_current_user
from app.services.document_analysis import DocumentAnalysisService, RequirementsExtractor

router = APIRouter(prefix="/document-analysis", tags=["Document Analysis"])


class TextAnalysisRequest(BaseModel):
    content: str
    document_type: str = "general"


class CompareDocumentsRequest(BaseModel):
    doc1_content: str
    doc2_content: str
    doc1_name: str = "Document 1"
    doc2_name: str = "Document 2"


@router.post("/analyze")
async def analyze_text(
    request: TextAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze provided text content."""
    analysis = DocumentAnalysisService.analyze_document(
        content=request.content,
        document_type=request.document_type,
    )
    return {"analysis": analysis}


@router.get("/analyze/{document_id}")
async def analyze_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a stored document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    analysis = DocumentAnalysisService.analyze_document(
        content=document.extracted_text,
        document_type=document.document_type.value,
    )

    return {
        "document_id": str(document_id),
        "document_name": document.original_filename,
        "analysis": analysis,
    }


@router.post("/compare")
async def compare_documents(
    request: CompareDocumentsRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare two documents."""
    comparison = DocumentAnalysisService.compare_documents(
        doc1_content=request.doc1_content,
        doc2_content=request.doc2_content,
        doc1_name=request.doc1_name,
        doc2_name=request.doc2_name,
    )
    return {"comparison": comparison}


@router.get("/compare/{doc1_id}/{doc2_id}")
async def compare_stored_documents(
    doc1_id: UUID,
    doc2_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare two stored documents."""
    doc1 = await db.get(Document, doc1_id)
    doc2 = await db.get(Document, doc2_id)

    if not doc1 or not doc2:
        raise HTTPException(status_code=404, detail="One or both documents not found")

    if not doc1.extracted_text or not doc2.extracted_text:
        raise HTTPException(status_code=400, detail="One or both documents have no extracted text")

    comparison = DocumentAnalysisService.compare_documents(
        doc1_content=doc1.extracted_text,
        doc2_content=doc2.extracted_text,
        doc1_name=doc1.original_filename,
        doc2_name=doc2.original_filename,
    )

    return {
        "document_1": {"id": str(doc1_id), "name": doc1.original_filename},
        "document_2": {"id": str(doc2_id), "name": doc2.original_filename},
        "comparison": comparison,
    }


@router.post("/extract-requirements")
async def extract_requirements(
    request: TextAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract requirements from text content."""
    requirements = RequirementsExtractor.extract_all_requirements(request.content)
    return {"requirements": requirements}


@router.get("/extract-requirements/{document_id}")
async def extract_document_requirements(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract requirements from a stored document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    requirements = RequirementsExtractor.extract_all_requirements(document.extracted_text)

    return {
        "document_id": str(document_id),
        "document_name": document.original_filename,
        "requirements": requirements,
    }


@router.get("/statistics/{document_id}")
async def get_document_statistics(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    analysis = DocumentAnalysisService.analyze_document(
        content=document.extracted_text,
        document_type=document.document_type.value,
    )

    return {
        "document_id": str(document_id),
        "document_name": document.original_filename,
        "statistics": analysis["statistics"],
        "readability": analysis["readability"],
    }
