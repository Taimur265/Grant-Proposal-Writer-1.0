"""Grant Proposal Writer - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth_router, projects_router, documents_router, proposals_router
from app.routers.templates import router as templates_router
from app.routers.analytics import router as analytics_router
from app.routers.budget import router as budget_router
from app.routers.search import router as search_router
from app.routers.collaboration import router as collaboration_router
from app.routers.timeline import router as timeline_router
from app.routers.document_analysis import router as document_analysis_router
from app.routers.export import router as export_router
from app.routers.funders import router as funders_router
from app.routers.workflow import router as workflow_router
from app.routers.ai_improvement import router as ai_router
from app.routers.settings import router as settings_router
from app.routers.team import router as team_router
from app.routers.compliance import router as compliance_router
from app.routers.calendar import router as calendar_router
from app.routers.letters import router as letters_router
from app.routers.audit import router as audit_router
from app.routers.widgets import router as widgets_router
from app.routers.ai_assistant import router as ai_assistant_router
from app.routers.stakeholders import router as stakeholders_router
from app.routers.reporting import router as reporting_router
from app.routers.risk import router as risk_router
from app.routers.logic_model import router as logic_model_router
from app.routers.resources import router as resources_router
from app.routers.needs_assessment import router as needs_assessment_router
from app.routers.goals_objectives import router as goals_objectives_router
from app.routers.evaluation import router as evaluation_router
from app.routers.sustainability import router as sustainability_router
from app.routers.funder_research import router as funder_research_router
from app.routers.application_tracking import router as application_tracking_router
from app.routers.narrative import router as narrative_router
from app.routers.work_plan import router as work_plan_router
from app.routers.post_award import router as post_award_router


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
app.include_router(templates_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(budget_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(collaboration_router, prefix="/api/v1")
app.include_router(timeline_router, prefix="/api/v1")
app.include_router(document_analysis_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(funders_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(team_router, prefix="/api/v1")
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(letters_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(widgets_router, prefix="/api/v1")
app.include_router(ai_assistant_router, prefix="/api/v1")
app.include_router(stakeholders_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")
app.include_router(logic_model_router, prefix="/api/v1")
app.include_router(resources_router, prefix="/api/v1")
app.include_router(needs_assessment_router, prefix="/api/v1")
app.include_router(goals_objectives_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")
app.include_router(sustainability_router, prefix="/api/v1")
app.include_router(funder_research_router, prefix="/api/v1")
app.include_router(application_tracking_router, prefix="/api/v1")
app.include_router(narrative_router, prefix="/api/v1")
app.include_router(work_plan_router, prefix="/api/v1")
app.include_router(post_award_router, prefix="/api/v1")


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
