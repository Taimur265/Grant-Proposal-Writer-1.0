"""Grant Proposal Writer - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, projects_router, documents_router, proposals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Grant Proposal Writer API - AI-powered grant proposal generation system.

    ## Features
    - **Document Management**: Upload and process guidelines, TORs, and beneficiary documents
    - **AI Proposal Generation**: Generate complete grant proposals based on uploaded documents
    - **Compliance Checking**: Verify proposals against guidelines
    - **Export**: Export proposals to various formats (DOCX, PDF, HTML, Markdown)

    ## Document Categories
    - **Guidelines Section**: Upload RFPs, guidelines, terms & conditions, eligibility criteria
    - **Beneficiary Section**: Upload organization profiles, financial statements, project descriptions
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(proposals_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/document-types")
async def get_document_types():
    """Get available document types and categories."""
    from app.models.document import DocumentType, DocumentCategory

    return {
        "categories": {
            "guidelines": {
                "name": "Guidelines & Requirements",
                "description": "Upload grant guidelines, RFPs, TORs, and eligibility criteria",
                "types": [
                    {"value": "guidelines", "label": "General Guidelines"},
                    {"value": "terms_conditions", "label": "Terms & Conditions"},
                    {"value": "tor", "label": "Terms of Reference (TOR)"},
                    {"value": "rfp", "label": "Request for Proposal (RFP)"},
                    {"value": "eligibility", "label": "Eligibility Criteria"},
                    {"value": "evaluation_criteria", "label": "Evaluation Criteria"},
                    {"value": "budget_template", "label": "Budget Template"},
                ],
            },
            "beneficiary": {
                "name": "Beneficiary Information",
                "description": "Upload organization and project details",
                "types": [
                    {"value": "organization_profile", "label": "Organization Profile"},
                    {"value": "registration_docs", "label": "Registration Documents"},
                    {"value": "financial_statements", "label": "Financial Statements"},
                    {"value": "project_description", "label": "Project Description"},
                    {"value": "beneficiary_data", "label": "Beneficiary Data"},
                    {"value": "impact_assessment", "label": "Impact Assessment"},
                    {"value": "team_cvs", "label": "Team CVs/Resumes"},
                    {"value": "past_performance", "label": "Past Performance"},
                    {"value": "letters_of_support", "label": "Letters of Support"},
                ],
            },
        },
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "max_file_size_mb": settings.MAX_UPLOAD_SIZE // 1024 // 1024,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
