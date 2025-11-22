"""Template service for grant proposal templates."""

from typing import Dict, List, Any, Optional


class TemplateService:
    """Service for managing proposal templates for different grant types."""

    # Comprehensive templates for different grant types
    TEMPLATES = {
        "federal": {
            "name": "Federal Grant Template",
            "description": "Template for federal government grants (NIH, NSF, DOE, etc.)",
            "sections": [
                {
                    "name": "Project Abstract",
                    "order": 1,
                    "max_words": 250,
                    "required": True,
                    "instructions": """
                        Provide a concise summary of the proposed project including:
                        - The problem or need being addressed
                        - Project goals and objectives
                        - Methods to be employed
                        - Expected outcomes and impact
                        - Target population and geographic area
                    """,
                },
                {
                    "name": "Specific Aims",
                    "order": 2,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        State the specific aims of the project:
                        - Primary aim with measurable objectives
                        - Secondary aims if applicable
                        - How aims address the funding opportunity
                        - Innovation and significance of the approach
                    """,
                },
                {
                    "name": "Background and Significance",
                    "order": 3,
                    "max_words": 2000,
                    "required": True,
                    "instructions": """
                        Provide comprehensive background including:
                        - Current state of knowledge in the field
                        - Gap in knowledge or unmet need
                        - Why this project is significant
                        - Relevant literature review
                        - How this advances the field
                    """,
                },
                {
                    "name": "Preliminary Studies/Progress Report",
                    "order": 4,
                    "max_words": 1500,
                    "required": True,
                    "instructions": """
                        Present preliminary data and prior work:
                        - Relevant preliminary studies conducted
                        - Data supporting feasibility
                        - Previous related projects and outcomes
                        - Pilot study results if applicable
                    """,
                },
                {
                    "name": "Research Design and Methods",
                    "order": 5,
                    "max_words": 3000,
                    "required": True,
                    "instructions": """
                        Detail the research methodology:
                        - Study design and rationale
                        - Data collection methods
                        - Analysis approaches
                        - Quality assurance procedures
                        - Potential limitations and alternatives
                    """,
                },
                {
                    "name": "Timeline and Milestones",
                    "order": 6,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Provide detailed project timeline:
                        - Key milestones and deliverables
                        - Gantt chart or timeline table
                        - Dependencies between activities
                        - Go/no-go decision points
                    """,
                },
                {
                    "name": "Personnel and Organization",
                    "order": 7,
                    "max_words": 1000,
                    "required": True,
                    "instructions": """
                        Describe project team and structure:
                        - Key personnel and roles
                        - Qualifications and expertise
                        - Time commitment
                        - Organizational structure
                        - Collaborators and consultants
                    """,
                },
                {
                    "name": "Facilities and Resources",
                    "order": 8,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Detail available resources:
                        - Laboratory/office space
                        - Equipment and technology
                        - Institutional support
                        - Access to data or populations
                    """,
                },
                {
                    "name": "Budget Justification",
                    "order": 9,
                    "max_words": 1500,
                    "required": True,
                    "instructions": """
                        Justify budget items:
                        - Personnel costs rationale
                        - Equipment and supplies needs
                        - Travel requirements
                        - Other direct costs
                        - Indirect costs explanation
                    """,
                },
                {
                    "name": "Human Subjects / IRB",
                    "order": 10,
                    "max_words": 500,
                    "required": False,
                    "instructions": """
                        If applicable, address human subjects:
                        - Protection of participants
                        - Informed consent procedures
                        - IRB status and approvals
                        - Data privacy measures
                    """,
                },
            ],
        },
        "foundation": {
            "name": "Foundation Grant Template",
            "description": "Template for private foundation grants",
            "sections": [
                {
                    "name": "Executive Summary",
                    "order": 1,
                    "max_words": 300,
                    "required": True,
                    "instructions": """
                        Compelling overview of the proposal:
                        - Organization and mission alignment
                        - The problem you're addressing
                        - Your proposed solution
                        - Expected impact
                        - Funding request amount
                    """,
                },
                {
                    "name": "Organization Background",
                    "order": 2,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Introduce your organization:
                        - Mission and vision
                        - History and accomplishments
                        - Current programs and services
                        - Geographic reach
                        - Organizational structure
                    """,
                },
                {
                    "name": "Statement of Need",
                    "order": 3,
                    "max_words": 800,
                    "required": True,
                    "instructions": """
                        Document the need:
                        - Problem description with data
                        - Who is affected and how
                        - Root causes
                        - Why action is needed now
                        - Consequences of inaction
                    """,
                },
                {
                    "name": "Project Description",
                    "order": 4,
                    "max_words": 1500,
                    "required": True,
                    "instructions": """
                        Detail the proposed project:
                        - Goals and objectives (SMART)
                        - Target population
                        - Activities and methods
                        - Implementation timeline
                        - Key partnerships
                    """,
                },
                {
                    "name": "Expected Outcomes and Impact",
                    "order": 5,
                    "max_words": 600,
                    "required": True,
                    "instructions": """
                        Describe expected results:
                        - Short-term outcomes
                        - Long-term impact
                        - Number of beneficiaries
                        - Community-level changes
                        - Broader significance
                    """,
                },
                {
                    "name": "Evaluation Plan",
                    "order": 6,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Explain how you'll measure success:
                        - Key performance indicators
                        - Data collection methods
                        - Evaluation timeline
                        - Use of findings
                        - External evaluator if applicable
                    """,
                },
                {
                    "name": "Budget Overview",
                    "order": 7,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Summarize the budget:
                        - Total project cost
                        - Amount requested
                        - Major budget categories
                        - Cost-effectiveness
                        - Other funding sources
                    """,
                },
                {
                    "name": "Sustainability",
                    "order": 8,
                    "max_words": 400,
                    "required": True,
                    "instructions": """
                        Address long-term sustainability:
                        - Post-grant funding strategy
                        - Revenue diversification
                        - Institutional embedding
                        - Scalability potential
                    """,
                },
            ],
        },
        "corporate": {
            "name": "Corporate Grant Template",
            "description": "Template for corporate/CSR funding",
            "sections": [
                {
                    "name": "Executive Summary",
                    "order": 1,
                    "max_words": 250,
                    "required": True,
                    "instructions": """
                        Brief, compelling overview:
                        - Project name and organization
                        - Alignment with corporate priorities
                        - Key outcomes and ROI
                        - Funding request
                    """,
                },
                {
                    "name": "Partnership Value Proposition",
                    "order": 2,
                    "max_words": 400,
                    "required": True,
                    "instructions": """
                        Why partner with your organization:
                        - Alignment with corporate values
                        - Brand visibility opportunities
                        - Employee engagement options
                        - Community impact metrics
                    """,
                },
                {
                    "name": "Project Overview",
                    "order": 3,
                    "max_words": 800,
                    "required": True,
                    "instructions": """
                        Concise project description:
                        - Problem and solution
                        - Target beneficiaries
                        - Key activities
                        - Timeline
                    """,
                },
                {
                    "name": "Impact Metrics",
                    "order": 4,
                    "max_words": 400,
                    "required": True,
                    "instructions": """
                        Quantifiable outcomes:
                        - Key metrics and targets
                        - Measurement methodology
                        - Reporting schedule
                        - Success indicators
                    """,
                },
                {
                    "name": "Recognition and Visibility",
                    "order": 5,
                    "max_words": 300,
                    "required": True,
                    "instructions": """
                        Corporate recognition opportunities:
                        - Naming rights
                        - Media coverage
                        - Social media mentions
                        - Event participation
                    """,
                },
                {
                    "name": "Budget Summary",
                    "order": 6,
                    "max_words": 300,
                    "required": True,
                    "instructions": """
                        Clear budget overview:
                        - Total cost and request
                        - Key line items
                        - Leverage/matching funds
                    """,
                },
            ],
        },
        "international": {
            "name": "International Development Template",
            "description": "Template for international development grants (USAID, World Bank, UN)",
            "sections": [
                {
                    "name": "Executive Summary",
                    "order": 1,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Comprehensive overview:
                        - Development challenge addressed
                        - Proposed intervention
                        - Target countries/regions
                        - Expected outcomes
                        - Budget and duration
                    """,
                },
                {
                    "name": "Development Context",
                    "order": 2,
                    "max_words": 1500,
                    "required": True,
                    "instructions": """
                        Situational analysis:
                        - Country/regional context
                        - Development indicators
                        - Policy environment
                        - Stakeholder landscape
                        - Previous interventions
                    """,
                },
                {
                    "name": "Theory of Change",
                    "order": 3,
                    "max_words": 800,
                    "required": True,
                    "instructions": """
                        Logical framework:
                        - Problem statement
                        - Causal analysis
                        - Intervention logic
                        - Assumptions and risks
                        - Results chain
                    """,
                },
                {
                    "name": "Technical Approach",
                    "order": 4,
                    "max_words": 2500,
                    "required": True,
                    "instructions": """
                        Detailed methodology:
                        - Intervention components
                        - Implementation strategy
                        - Geographic targeting
                        - Beneficiary selection
                        - Technical innovations
                    """,
                },
                {
                    "name": "Monitoring, Evaluation, and Learning",
                    "order": 5,
                    "max_words": 1000,
                    "required": True,
                    "instructions": """
                        MEL framework:
                        - Indicators and targets
                        - Data collection methods
                        - Learning agenda
                        - Adaptive management
                        - Knowledge sharing
                    """,
                },
                {
                    "name": "Sustainability and Exit Strategy",
                    "order": 6,
                    "max_words": 600,
                    "required": True,
                    "instructions": """
                        Long-term sustainability:
                        - Local ownership
                        - Capacity building
                        - Policy integration
                        - Exit timeline
                    """,
                },
                {
                    "name": "Gender and Social Inclusion",
                    "order": 7,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Cross-cutting issues:
                        - Gender analysis
                        - Inclusion strategy
                        - Do no harm
                        - Safeguarding measures
                    """,
                },
                {
                    "name": "Environmental Compliance",
                    "order": 8,
                    "max_words": 400,
                    "required": False,
                    "instructions": """
                        Environmental considerations:
                        - Environmental screening
                        - Climate resilience
                        - Mitigation measures
                    """,
                },
                {
                    "name": "Institutional Capacity",
                    "order": 9,
                    "max_words": 800,
                    "required": True,
                    "instructions": """
                        Organizational qualifications:
                        - Relevant experience
                        - In-country presence
                        - Past performance
                        - Key personnel
                        - Partners and subcontractors
                    """,
                },
                {
                    "name": "Budget Narrative",
                    "order": 10,
                    "max_words": 1000,
                    "required": True,
                    "instructions": """
                        Detailed budget justification:
                        - Cost categories
                        - Unit costs and quantities
                        - Cost share/leverage
                        - Cost realism
                    """,
                },
            ],
        },
        "research": {
            "name": "Academic Research Template",
            "description": "Template for university/academic research grants",
            "sections": [
                {
                    "name": "Abstract",
                    "order": 1,
                    "max_words": 300,
                    "required": True,
                    "instructions": """
                        Research summary:
                        - Research question
                        - Methodology
                        - Expected contributions
                        - Broader impacts
                    """,
                },
                {
                    "name": "Introduction and Literature Review",
                    "order": 2,
                    "max_words": 2000,
                    "required": True,
                    "instructions": """
                        Scholarly context:
                        - Research problem
                        - Literature synthesis
                        - Theoretical framework
                        - Research gaps
                    """,
                },
                {
                    "name": "Research Questions and Hypotheses",
                    "order": 3,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Clear research focus:
                        - Primary questions
                        - Hypotheses if applicable
                        - Variables and constructs
                    """,
                },
                {
                    "name": "Methodology",
                    "order": 4,
                    "max_words": 2500,
                    "required": True,
                    "instructions": """
                        Research design:
                        - Research approach
                        - Sample and sampling
                        - Data collection
                        - Analysis methods
                        - Validity and reliability
                    """,
                },
                {
                    "name": "Timeline",
                    "order": 5,
                    "max_words": 400,
                    "required": True,
                    "instructions": """
                        Research schedule:
                        - Phases and activities
                        - Milestones
                        - Deliverables
                    """,
                },
                {
                    "name": "Expected Contributions",
                    "order": 6,
                    "max_words": 600,
                    "required": True,
                    "instructions": """
                        Significance of research:
                        - Theoretical contributions
                        - Practical implications
                        - Knowledge advancement
                        - Dissemination plan
                    """,
                },
                {
                    "name": "Researcher Qualifications",
                    "order": 7,
                    "max_words": 500,
                    "required": True,
                    "instructions": """
                        Team expertise:
                        - PI qualifications
                        - Research team
                        - Relevant publications
                        - Prior grants
                    """,
                },
                {
                    "name": "Budget Justification",
                    "order": 8,
                    "max_words": 800,
                    "required": True,
                    "instructions": """
                        Resource needs:
                        - Personnel
                        - Equipment
                        - Travel
                        - Participant costs
                        - Other expenses
                    """,
                },
            ],
        },
        "default": {
            "name": "General Grant Template",
            "description": "General purpose grant proposal template",
            "sections": [
                {
                    "name": "Executive Summary",
                    "order": 1,
                    "max_words": 500,
                    "required": True,
                    "instructions": "Provide a compelling overview of the entire proposal.",
                },
                {
                    "name": "Statement of Need",
                    "order": 2,
                    "max_words": 1000,
                    "required": True,
                    "instructions": "Document the problem using data and evidence.",
                },
                {
                    "name": "Project Description",
                    "order": 3,
                    "max_words": 2000,
                    "required": True,
                    "instructions": "Detail goals, objectives, activities, and timeline.",
                },
                {
                    "name": "Goals and Objectives",
                    "order": 4,
                    "max_words": 800,
                    "required": True,
                    "instructions": "List SMART goals and measurable objectives.",
                },
                {
                    "name": "Methods and Timeline",
                    "order": 5,
                    "max_words": 1500,
                    "required": True,
                    "instructions": "Describe implementation approach and schedule.",
                },
                {
                    "name": "Evaluation Plan",
                    "order": 6,
                    "max_words": 800,
                    "required": True,
                    "instructions": "Explain how success will be measured.",
                },
                {
                    "name": "Organizational Capacity",
                    "order": 7,
                    "max_words": 1000,
                    "required": True,
                    "instructions": "Demonstrate ability to execute the project.",
                },
                {
                    "name": "Budget Narrative",
                    "order": 8,
                    "max_words": 1000,
                    "required": True,
                    "instructions": "Justify budget items and demonstrate cost-effectiveness.",
                },
                {
                    "name": "Sustainability Plan",
                    "order": 9,
                    "max_words": 600,
                    "required": False,
                    "instructions": "Address long-term sustainability after grant period.",
                },
                {
                    "name": "Conclusion",
                    "order": 10,
                    "max_words": 300,
                    "required": True,
                    "instructions": "Summarize key points and make final appeal.",
                },
            ],
        },
    }

    @classmethod
    def get_template(cls, grant_type: str) -> Dict[str, Any]:
        """Get template by grant type."""
        return cls.TEMPLATES.get(grant_type, cls.TEMPLATES["default"])

    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available templates."""
        return cls.TEMPLATES

    @classmethod
    def get_template_names(cls) -> List[Dict[str, str]]:
        """Get list of template names and descriptions."""
        return [
            {
                "id": key,
                "name": template["name"],
                "description": template["description"],
            }
            for key, template in cls.TEMPLATES.items()
        ]

    @classmethod
    def get_sections_for_type(cls, grant_type: str) -> List[Dict[str, Any]]:
        """Get sections for a specific grant type."""
        template = cls.get_template(grant_type)
        return template.get("sections", [])

    @classmethod
    def customize_template(
        cls,
        grant_type: str,
        custom_sections: Optional[List[str]] = None,
        max_words: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Customize template sections based on requirements."""
        sections = cls.get_sections_for_type(grant_type)

        # Filter sections if custom list provided
        if custom_sections:
            sections = [s for s in sections if s["name"] in custom_sections]

        # Apply custom max words
        if max_words:
            for section in sections:
                section["max_words"] = min(section.get("max_words", max_words), max_words)

        return sections
