"""Proposal generation service."""

from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, DocumentCategory
from app.models.proposal import Proposal, ProposalSection, ProposalStatus
from app.models.project import Project
from app.services.ai_service import AIService
from app.services.document_processor import DocumentProcessor


class ProposalGenerator:
    """Service for generating grant proposals using AI."""

    # Standard proposal sections for different grant types
    STANDARD_SECTIONS = {
        "default": [
            {"name": "Executive Summary", "order": 1, "max_words": 500, "required": True},
            {"name": "Statement of Need", "order": 2, "max_words": 1000, "required": True},
            {"name": "Project Description", "order": 3, "max_words": 2000, "required": True},
            {"name": "Goals and Objectives", "order": 4, "max_words": 800, "required": True},
            {"name": "Methods and Timeline", "order": 5, "max_words": 1500, "required": True},
            {"name": "Evaluation Plan", "order": 6, "max_words": 800, "required": True},
            {"name": "Organizational Capacity", "order": 7, "max_words": 1000, "required": True},
            {"name": "Budget Narrative", "order": 8, "max_words": 1000, "required": True},
            {"name": "Sustainability Plan", "order": 9, "max_words": 600, "required": False},
            {"name": "Conclusion", "order": 10, "max_words": 300, "required": True},
        ],
        "federal": [
            {"name": "Abstract", "order": 1, "max_words": 250, "required": True},
            {"name": "Specific Aims", "order": 2, "max_words": 500, "required": True},
            {"name": "Background and Significance", "order": 3, "max_words": 2000, "required": True},
            {"name": "Preliminary Studies", "order": 4, "max_words": 1500, "required": True},
            {"name": "Research Design and Methods", "order": 5, "max_words": 3000, "required": True},
            {"name": "Timeline", "order": 6, "max_words": 500, "required": True},
            {"name": "Personnel and Organization", "order": 7, "max_words": 1000, "required": True},
            {"name": "Facilities and Resources", "order": 8, "max_words": 500, "required": True},
            {"name": "Budget Justification", "order": 9, "max_words": 1500, "required": True},
        ],
        "foundation": [
            {"name": "Executive Summary", "order": 1, "max_words": 300, "required": True},
            {"name": "Organization Background", "order": 2, "max_words": 500, "required": True},
            {"name": "Problem Statement", "order": 3, "max_words": 800, "required": True},
            {"name": "Project Description", "order": 4, "max_words": 1500, "required": True},
            {"name": "Expected Outcomes", "order": 5, "max_words": 600, "required": True},
            {"name": "Evaluation", "order": 6, "max_words": 500, "required": True},
            {"name": "Budget Overview", "order": 7, "max_words": 500, "required": True},
            {"name": "Future Funding", "order": 8, "max_words": 300, "required": False},
        ],
    }

    SECTION_PROMPTS = {
        "Executive Summary": """Write a compelling executive summary that:
- Opens with a powerful hook about the problem
- Briefly describes the proposed solution
- Highlights expected outcomes and impact
- States the funding request and organization qualifications
- Creates urgency and importance""",

        "Statement of Need": """Write a statement of need that:
- Uses data and statistics to demonstrate the problem
- Shows the gap between current situation and desired state
- Connects the problem to the funder's priorities
- Establishes credibility through research and evidence
- Creates emotional resonance while remaining professional""",

        "Project Description": """Write a detailed project description that:
- Clearly explains what will be done
- Describes the target population and how they'll be served
- Outlines the approach and methodology
- Explains why this approach will work
- Differentiates from other solutions""",

        "Goals and Objectives": """Write goals and objectives that are:
- SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Aligned with the funder's priorities
- Logically connected to the statement of need
- Realistic given the budget and timeline
- Include both short-term and long-term goals""",

        "Methods and Timeline": """Write a methods and timeline section that:
- Describes specific activities and interventions
- Provides a realistic timeline with milestones
- Identifies responsible parties for each activity
- Shows logical flow from activities to outcomes
- Addresses potential challenges and mitigation strategies""",

        "Evaluation Plan": """Write an evaluation plan that:
- Defines clear success metrics
- Describes data collection methods
- Explains how progress will be monitored
- Includes both process and outcome evaluation
- Shows commitment to learning and improvement""",

        "Organizational Capacity": """Write about organizational capacity including:
- Relevant experience and track record
- Staff qualifications and expertise
- Partnerships and collaborations
- Financial health and management
- Previous grant successes""",

        "Budget Narrative": """Write a budget narrative that:
- Justifies each major budget item
- Shows cost-effectiveness
- Aligns expenses with project activities
- Explains any matching funds or in-kind contributions
- Demonstrates fiscal responsibility""",

        "Sustainability Plan": """Write a sustainability plan that:
- Addresses long-term funding strategies
- Shows how impact will continue after grant period
- Identifies potential future funders
- Describes plans for scaling or replication
- Demonstrates organizational commitment""",

        "Conclusion": """Write a conclusion that:
- Reinforces the key points of the proposal
- Restates the funding request
- Emphasizes expected impact
- Expresses appreciation for consideration
- Ends with a strong call to action""",
    }

    def __init__(self, db: AsyncSession, ai_service: Optional[AIService] = None):
        self.db = db
        self.ai_service = ai_service or AIService()

    async def generate_proposal(
        self,
        project_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        tone: str = "professional",
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        include_sections: Optional[List[str]] = None,
        max_words_per_section: Optional[int] = None,
    ) -> Proposal:
        """Generate a complete grant proposal."""

        # Get project
        project = await self.db.get(Project, project_id)
        if not project:
            raise ValueError("Project not found")

        # Get all documents for the project
        guidelines_docs = await self._get_documents(project_id, DocumentCategory.GUIDELINES)
        beneficiary_docs = await self._get_documents(project_id, DocumentCategory.BENEFICIARY)

        # Combine document content
        guidelines_content = self._combine_document_content(guidelines_docs)
        beneficiary_content = self._combine_document_content(beneficiary_docs)

        # Analyze guidelines to extract requirements
        guidelines_analysis = DocumentProcessor.analyze_guidelines(guidelines_content)

        # Determine sections based on grant type or guidelines
        sections_config = self._determine_sections(
            project.grant_type,
            guidelines_analysis,
            include_sections,
            max_words_per_section,
        )

        # Create proposal record
        proposal = Proposal(
            title=title or f"Grant Proposal - {project.name}",
            project_id=project_id,
            created_by=user_id,
            status=ProposalStatus.GENERATING,
            ai_model_used=self.ai_service.model,
            generation_params={
                "tone": tone,
                "focus_areas": focus_areas,
                "custom_instructions": custom_instructions,
            },
        )
        self.db.add(proposal)
        await self.db.flush()

        # Generate each section
        full_content_parts = []
        for section_config in sections_config:
            section_content = await self._generate_section(
                section_name=section_config["name"],
                guidelines_content=guidelines_content,
                beneficiary_content=beneficiary_content,
                guidelines_analysis=guidelines_analysis,
                tone=tone,
                focus_areas=focus_areas,
                custom_instructions=custom_instructions,
                max_words=section_config.get("max_words"),
            )

            # Create section record
            section = ProposalSection(
                proposal_id=proposal.id,
                section_name=section_config["name"],
                section_order=section_config["order"],
                content=section_content,
                word_count=len(section_content.split()),
                max_words=section_config.get("max_words"),
                is_required=section_config.get("required", True),
                is_complete=True,
            )
            self.db.add(section)
            full_content_parts.append(f"## {section_config['name']}\n\n{section_content}")

        # Generate executive summary based on all content
        executive_summary = await self.ai_service.generate_executive_summary(
            "\n\n".join(full_content_parts),
            max_words=500,
        )

        # Update proposal
        proposal.executive_summary = executive_summary
        proposal.full_content = "\n\n".join(full_content_parts)
        proposal.word_count = sum(len(part.split()) for part in full_content_parts)
        proposal.status = ProposalStatus.DRAFT

        # Check compliance
        compliance_result = await self.ai_service.check_compliance(
            proposal.full_content,
            guidelines_content,
        )
        if isinstance(compliance_result.get("score"), (int, float)):
            proposal.compliance_score = compliance_result["score"]

        await self.db.flush()
        await self.db.refresh(proposal)

        return proposal

    async def _get_documents(
        self,
        project_id: UUID,
        category: DocumentCategory,
    ) -> List[Document]:
        """Get documents by project and category."""
        result = await self.db.execute(
            select(Document).where(
                Document.project_id == project_id,
                Document.category == category,
                Document.processing_status == "completed",
            )
        )
        return result.scalars().all()

    def _combine_document_content(self, documents: List[Document]) -> str:
        """Combine content from multiple documents."""
        content_parts = []
        for doc in documents:
            if doc.extracted_text:
                content_parts.append(f"=== {doc.original_filename} ===\n{doc.extracted_text}")
        return "\n\n".join(content_parts)

    def _determine_sections(
        self,
        grant_type: Optional[str],
        guidelines_analysis: Dict[str, Any],
        include_sections: Optional[List[str]],
        max_words_per_section: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Determine proposal sections based on grant type and guidelines."""
        # Get base sections for grant type
        base_sections = self.STANDARD_SECTIONS.get(
            grant_type or "default",
            self.STANDARD_SECTIONS["default"]
        )

        # If sections specified in guidelines, use those
        if guidelines_analysis.get("sections_required"):
            custom_sections = []
            for i, section_name in enumerate(guidelines_analysis["sections_required"], 1):
                custom_sections.append({
                    "name": section_name,
                    "order": i,
                    "max_words": max_words_per_section or 1000,
                    "required": True,
                })
            if custom_sections:
                return custom_sections

        # Filter sections if specific ones requested
        if include_sections:
            base_sections = [
                s for s in base_sections
                if s["name"] in include_sections
            ]

        # Apply custom max words if specified
        if max_words_per_section:
            for section in base_sections:
                section["max_words"] = max_words_per_section

        return base_sections

    async def _generate_section(
        self,
        section_name: str,
        guidelines_content: str,
        beneficiary_content: str,
        guidelines_analysis: Dict[str, Any],
        tone: str,
        focus_areas: Optional[List[str]],
        custom_instructions: Optional[str],
        max_words: Optional[int],
    ) -> str:
        """Generate content for a specific proposal section."""
        section_prompt = self.SECTION_PROMPTS.get(
            section_name,
            f"Write the {section_name} section following standard grant writing best practices."
        )

        prompt = f"""You are writing the "{section_name}" section of a grant proposal.

GUIDELINES AND REQUIREMENTS:
{guidelines_content[:4000]}

ORGANIZATION/BENEFICIARY INFORMATION:
{beneficiary_content[:4000]}

KEY REQUIREMENTS FROM GUIDELINES:
- Eligibility: {', '.join(guidelines_analysis.get('eligibility_criteria', [])[:5])}
- Evaluation Criteria: {', '.join(guidelines_analysis.get('evaluation_criteria', [])[:5])}
- Requirements: {', '.join(guidelines_analysis.get('requirements', [])[:5])}

SECTION INSTRUCTIONS:
{section_prompt}

ADDITIONAL REQUIREMENTS:
- Tone: {tone}
{f'- Focus Areas: {", ".join(focus_areas)}' if focus_areas else ''}
{f'- Custom Instructions: {custom_instructions}' if custom_instructions else ''}
{f'- Maximum Words: {max_words}' if max_words else ''}

Write this section now. Be specific, use data where available, and align with the guidelines."""

        system_prompt = """You are an expert grant writer with decades of experience
securing funding from federal agencies, foundations, and corporations. Write compelling,
professional content that addresses funder priorities and demonstrates strong understanding
of the guidelines. Use specific examples and measurable outcomes."""

        content = await self.ai_service.generate_text(
            prompt,
            system_prompt,
            max_tokens=max_words * 2 if max_words else 2000,
            temperature=0.7,
        )

        return content

    async def regenerate_section(
        self,
        proposal_id: UUID,
        section_id: UUID,
        feedback: Optional[str] = None,
    ) -> ProposalSection:
        """Regenerate a specific section with optional feedback."""
        # Get section and proposal
        section = await self.db.get(ProposalSection, section_id)
        if not section or section.proposal_id != proposal_id:
            raise ValueError("Section not found")

        proposal = await self.db.get(Proposal, proposal_id)

        # Get documents
        guidelines_docs = await self._get_documents(proposal.project_id, DocumentCategory.GUIDELINES)
        guidelines_content = self._combine_document_content(guidelines_docs)

        # Improve section
        improved_content = await self.ai_service.improve_section(
            section.content,
            section.section_name,
            guidelines_content,
            feedback,
        )

        section.content = improved_content
        section.word_count = len(improved_content.split())
        section.ai_suggestions = None  # Clear old suggestions

        await self.db.flush()
        await self.db.refresh(section)

        return section
