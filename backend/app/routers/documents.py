"""Document API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.document import Document, DocumentType, DocumentCategory
from app.models.project import Project
from app.models.user import User
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentUpdate, DocumentContent, DocumentAnalysis
)
from app.routers.auth import get_current_user
from app.services.storage import StorageService
from app.services.document_processor import DocumentProcessor
from app.services.ai_service import AIService
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])


async def process_document_background(
    document_id: UUID,
    file_path: str,
    db_url: str,
):
    """Background task to process document."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        document = await session.get(Document, document_id)
        if not document:
            return

        try:
            document.processing_status = "processing"
            await session.commit()

            # Process document
            storage = StorageService()
            full_path = storage.get_full_path(file_path)
            result = await DocumentProcessor.process_document(full_path)

            # Update document with extracted content
            document.extracted_text = result.get("extracted_text", "")
            document.extracted_metadata = result.get("metadata", {})
            document.key_points = result.get("key_points", [])

            # Generate AI summary if text was extracted
            if document.extracted_text:
                ai_service = AIService()
                analysis_type = "guidelines" if document.category == DocumentCategory.GUIDELINES else "beneficiary"
                try:
                    analysis = await ai_service.analyze_document(
                        document.extracted_text[:10000],
                        analysis_type,
                    )
                    if isinstance(analysis, dict):
                        document.summary = analysis.get("summary", str(analysis.get("analysis", "")))
                except Exception:
                    pass  # AI analysis is optional

            document.processing_status = "completed"
            document.processed_at = datetime.utcnow()

        except Exception as e:
            document.processing_status = "failed"
            document.processing_error = str(e)

        await session.commit()

    await engine.dispose()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: UUID = Form(...),
    category: DocumentCategory = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to a project."""
    # Verify project exists and user has access
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )

    # Save file
    storage = StorageService()
    stored_filename, file_path = await storage.save_file(
        file.file,
        file.filename,
        str(project_id),
        category.value,
    )

    # Create document record
    document = Document(
        filename=stored_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_extension=file_ext,
        document_type=document_type,
        category=category,
        project_id=project_id,
        uploaded_by=current_user.id,
        processing_status="pending",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Start background processing
    background_tasks.add_task(
        process_document_background,
        document.id,
        file_path,
        settings.DATABASE_URL,
    )

    return document


@router.post("/upload/batch", response_model=List[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project_id: UUID = Form(...),
    category: DocumentCategory = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple documents at once."""
    # Verify project exists and user has access
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    uploaded_documents = []
    storage = StorageService()

    for file in files:
        # Validate file extension
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            continue  # Skip unsupported files

        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_UPLOAD_SIZE:
            continue  # Skip oversized files

        # Save file
        stored_filename, file_path = await storage.save_file(
            file.file,
            file.filename,
            str(project_id),
            category.value,
        )

        # Create document record
        document = Document(
            filename=stored_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            file_extension=file_ext,
            document_type=DocumentType.OTHER,
            category=category,
            project_id=project_id,
            uploaded_by=current_user.id,
            processing_status="pending",
        )
        db.add(document)
        await db.flush()
        await db.refresh(document)

        uploaded_documents.append(document)

        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document.id,
            file_path,
            settings.DATABASE_URL,
        )

    return uploaded_documents


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[DocumentCategory] = None,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents for a project."""
    # Verify project access
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build query
    query = select(Document).where(Document.project_id == project_id)

    if category:
        query = query.where(Document.category == category)
    if document_type:
        query = query.where(Document.document_type == document_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Apply pagination
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify project access
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return document


@router.get("/{document_id}/content", response_model=DocumentContent)
async def get_document_content(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get extracted content from a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify project access
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if document.processing_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Document processing not complete. Status: {document.processing_status}",
        )

    return DocumentContent(
        id=document.id,
        extracted_text=document.extracted_text,
        summary=document.summary,
        key_points=document.key_points,
        extracted_metadata=document.extracted_metadata,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify project access
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in document_update.model_dump(exclude_unset=True).items():
        setattr(document, field, value)

    await db.flush()
    await db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify project access
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete file from storage
    storage = StorageService()
    await storage.delete_file(document.file_path)

    await db.delete(document)


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reprocess a document to extract content again."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify project access
    project = await db.get(Project, document.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Reset processing status
    document.processing_status = "pending"
    document.processing_error = None
    await db.flush()

    # Start background processing
    background_tasks.add_task(
        process_document_background,
        document.id,
        document.file_path,
        settings.DATABASE_URL,
    )

    await db.refresh(document)
    return document
