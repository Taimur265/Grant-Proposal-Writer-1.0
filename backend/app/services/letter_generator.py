"""Letter of support and template generation service."""

from typing import Dict, Any, List, Optional
from datetime import datetime


class LetterGenerator:
    """Service for generating letters of support and other grant-related documents."""

    # Letter templates
    LETTER_TEMPLATES = {
        "support_general": {
            "name": "General Letter of Support",
            "description": "Standard letter of support from a partner organization",
            "required_fields": ["organization_name", "project_name", "applicant_name"],
        },
        "support_community": {
            "name": "Community Support Letter",
            "description": "Letter from community members or groups",
            "required_fields": ["community_name", "project_name", "applicant_name"],
        },
        "support_government": {
            "name": "Government Agency Support",
            "description": "Letter from government agency or official",
            "required_fields": ["agency_name", "official_name", "project_name"],
        },
        "commitment_financial": {
            "name": "Financial Commitment Letter",
            "description": "Letter committing financial resources or in-kind support",
            "required_fields": ["organization_name", "commitment_amount", "project_name"],
        },
        "commitment_partnership": {
            "name": "Partnership Commitment Letter",
            "description": "Letter establishing partnership terms",
            "required_fields": ["partner_name", "role_description", "project_name"],
        },
        "mou": {
            "name": "Memorandum of Understanding",
            "description": "Formal MOU between organizations",
            "required_fields": ["party_a_name", "party_b_name", "purpose"],
        },
    }

    @classmethod
    def generate_letter(
        cls,
        template_type: str,
        data: Dict[str, Any],
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a letter from template."""
        if template_type not in cls.LETTER_TEMPLATES:
            return {"error": f"Unknown template type: {template_type}"}

        template = cls.LETTER_TEMPLATES[template_type]

        # Check required fields
        missing_fields = [
            field for field in template["required_fields"]
            if not data.get(field)
        ]
        if missing_fields:
            return {
                "error": "Missing required fields",
                "missing_fields": missing_fields,
            }

        # Generate letter content based on template type
        if template_type == "support_general":
            content = cls._generate_general_support(data)
        elif template_type == "support_community":
            content = cls._generate_community_support(data)
        elif template_type == "support_government":
            content = cls._generate_government_support(data)
        elif template_type == "commitment_financial":
            content = cls._generate_financial_commitment(data)
        elif template_type == "commitment_partnership":
            content = cls._generate_partnership_commitment(data)
        elif template_type == "mou":
            content = cls._generate_mou(data)
        else:
            content = cls._generate_generic_letter(data)

        return {
            "template_type": template_type,
            "template_name": template["name"],
            "content": content,
            "generated_at": datetime.utcnow().isoformat(),
            "data_used": data,
        }

    @classmethod
    def _generate_general_support(cls, data: Dict) -> str:
        """Generate general letter of support."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('organization_name', '[Organization Name]')}
{data.get('organization_address', '[Address]')}
{data.get('city_state_zip', '[City, State ZIP]')}

{date}

{data.get('recipient_name', 'To Whom It May Concern')}
{data.get('recipient_title', '')}
{data.get('recipient_organization', '')}
{data.get('recipient_address', '')}

RE: Letter of Support for {data.get('project_name', '[Project Name]')}

Dear {data.get('salutation', 'Grant Review Committee')}:

On behalf of {data.get('organization_name', '[Organization Name]')}, I am pleased to write this letter in support of {data.get('applicant_name', '[Applicant Organization]')}'s proposal for {data.get('project_name', '[Project Name]')}.

{data.get('relationship_description', 'Our organization has worked closely with the applicant and has witnessed their dedication to serving the community.')}

{data.get('project_support_description', 'We believe this project will significantly benefit our community by addressing critical needs and creating positive impact.')}

{data.get('commitment_description', 'We are committed to supporting this project through our continued partnership and collaboration.')}

{data.get('additional_paragraphs', '')}

We strongly endorse this proposal and look forward to the positive outcomes this project will generate. Please do not hesitate to contact me if you require any additional information.

Sincerely,

{data.get('signatory_name', '[Name]')}
{data.get('signatory_title', '[Title]')}
{data.get('organization_name', '[Organization Name]')}
{data.get('signatory_email', '[Email]')}
{data.get('signatory_phone', '[Phone]')}
""".strip()

    @classmethod
    def _generate_community_support(cls, data: Dict) -> str:
        """Generate community support letter."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('community_name', '[Community/Group Name]')}
{data.get('address', '[Address]')}

{date}

RE: Community Support for {data.get('project_name', '[Project Name]')}

Dear Grant Review Committee:

As {data.get('role', 'representatives')} of {data.get('community_name', '[Community/Group Name]')}, we write to express our wholehearted support for {data.get('applicant_name', '[Applicant Organization]')}'s proposed {data.get('project_name', '[Project Name]')}.

Our community {data.get('community_description', 'has identified significant needs that this project directly addresses')}. {data.get('need_description', 'The proposed initiative will provide critical resources and support to our community members.')}

{data.get('impact_description', 'We anticipate that this project will create meaningful, positive change in our community.')}

{data.get('participation_commitment', 'We are committed to actively participating in and supporting this project through community engagement and outreach.')}

{data.get('testimonials', '')}

We urge you to fund this important project that will benefit {data.get('beneficiary_count', 'many')} members of our community.

Respectfully,

{data.get('signatory_name', '[Name(s)]')}
{data.get('signatory_role', '[Role/Position]')}
{data.get('community_name', '[Community/Group Name]')}
""".strip()

    @classmethod
    def _generate_government_support(cls, data: Dict) -> str:
        """Generate government agency support letter."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('agency_name', '[Government Agency]')}
{data.get('agency_address', '[Address]')}

{date}

RE: {data.get('agency_name', '[Agency]')} Support for {data.get('project_name', '[Project Name]')}

Dear Funding Organization:

The {data.get('agency_name', '[Government Agency]')} is pleased to provide this letter of support for {data.get('applicant_name', '[Applicant Organization]')}'s proposal entitled "{data.get('project_name', '[Project Name]')}".

{data.get('agency_mission', 'Our agency is committed to supporting initiatives that align with our mission to serve the public interest.')}

{data.get('alignment_description', 'This project aligns with our strategic priorities and addresses needs within our jurisdiction.')}

{data.get('support_description', 'We will support this project by providing access to relevant data, coordination with our programs, and technical guidance as appropriate.')}

{data.get('commitment_specifics', '')}

We believe this project will contribute significantly to {data.get('impact_area', 'our shared goals')} and we look forward to its successful implementation.

Sincerely,

{data.get('official_name', '[Official Name]')}
{data.get('official_title', '[Title]')}
{data.get('agency_name', '[Agency]')}
""".strip()

    @classmethod
    def _generate_financial_commitment(cls, data: Dict) -> str:
        """Generate financial commitment letter."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('organization_name', '[Organization Name]')}
{data.get('address', '[Address]')}

{date}

RE: Financial Commitment for {data.get('project_name', '[Project Name]')}

Dear Grant Review Committee:

This letter confirms the financial commitment of {data.get('organization_name', '[Organization Name]')} to {data.get('applicant_name', '[Applicant Organization]')}'s {data.get('project_name', '[Project Name]')}.

We hereby commit to providing:

{data.get('cash_commitment', 'Cash contribution: $[Amount]')}

{data.get('inkind_commitment', 'In-kind contribution: [Description] valued at $[Amount]')}

These resources will be provided {data.get('timing', 'over the course of the project period')} and will be used for {data.get('use_description', 'project implementation and support')}.

This commitment is {data.get('conditionality', 'contingent upon the project receiving full funding from the grant program')}.

{data.get('additional_terms', '')}

Please contact us if you require any additional documentation regarding this commitment.

Sincerely,

{data.get('signatory_name', '[Name]')}
{data.get('signatory_title', '[Title]')}
{data.get('organization_name', '[Organization Name]')}
""".strip()

    @classmethod
    def _generate_partnership_commitment(cls, data: Dict) -> str:
        """Generate partnership commitment letter."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('partner_name', '[Partner Organization]')}
{data.get('address', '[Address]')}

{date}

RE: Partnership Commitment for {data.get('project_name', '[Project Name]')}

Dear Grant Review Committee:

{data.get('partner_name', '[Partner Organization]')} is committed to partnering with {data.get('applicant_name', '[Applicant Organization]')} on the proposed {data.get('project_name', '[Project Name]')}.

Partnership Role and Responsibilities:

{data.get('role_description', 'Our organization will serve as a key partner, contributing expertise and resources to project implementation.')}

Specific Contributions:
{data.get('contributions', '- [List specific contributions]')}

Partnership History:
{data.get('partnership_history', 'Our organizations have a history of successful collaboration.')}

Expected Outcomes:
{data.get('expected_outcomes', 'Through this partnership, we expect to achieve significant positive impact for our shared beneficiaries.')}

{data.get('additional_commitments', '')}

We look forward to this collaboration and are confident in the project's potential for success.

Sincerely,

{data.get('signatory_name', '[Name]')}
{data.get('signatory_title', '[Title]')}
{data.get('partner_name', '[Partner Organization]')}
""".strip()

    @classmethod
    def _generate_mou(cls, data: Dict) -> str:
        """Generate Memorandum of Understanding."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
MEMORANDUM OF UNDERSTANDING

Between

{data.get('party_a_name', '[Party A Name]')}
(hereinafter referred to as "Party A")

And

{data.get('party_b_name', '[Party B Name]')}
(hereinafter referred to as "Party B")

Date: {date}

1. PURPOSE

{data.get('purpose', 'This Memorandum of Understanding (MOU) establishes a framework for collaboration between the parties.')}

2. BACKGROUND

{data.get('background', 'Both parties recognize the mutual benefits of working together on shared goals and objectives.')}

3. SCOPE OF COLLABORATION

{data.get('scope', 'The parties agree to collaborate on [specific activities and areas].')}

4. ROLES AND RESPONSIBILITIES

Party A shall:
{data.get('party_a_responsibilities', '- [List responsibilities]')}

Party B shall:
{data.get('party_b_responsibilities', '- [List responsibilities]')}

5. RESOURCES

{data.get('resources', 'Each party will contribute resources as follows: [specify resources]')}

6. DURATION

This MOU shall be effective from {data.get('start_date', '[Start Date]')} to {data.get('end_date', '[End Date]')}.

7. MODIFICATION AND TERMINATION

{data.get('modification_terms', 'This MOU may be modified by mutual written consent of both parties. Either party may terminate this MOU with 30 days written notice.')}

8. CONFIDENTIALITY

{data.get('confidentiality', 'Both parties agree to maintain confidentiality of any proprietary or sensitive information shared under this MOU.')}

9. SIGNATURES

For Party A:

_________________________
{data.get('party_a_signatory', '[Name, Title]')}
Date: _______________

For Party B:

_________________________
{data.get('party_b_signatory', '[Name, Title]')}
Date: _______________
""".strip()

    @classmethod
    def _generate_generic_letter(cls, data: Dict) -> str:
        """Generate generic letter."""
        date = data.get("date", datetime.now().strftime("%B %d, %Y"))
        return f"""
{data.get('sender_name', '[Sender Name]')}
{data.get('sender_address', '[Address]')}

{date}

{data.get('recipient_name', '[Recipient Name]')}
{data.get('recipient_address', '[Address]')}

RE: {data.get('subject', '[Subject]')}

Dear {data.get('salutation', '[Recipient]')}:

{data.get('body', '[Letter body content]')}

Sincerely,

{data.get('signatory_name', '[Name]')}
{data.get('signatory_title', '[Title]')}
""".strip()

    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """List all available letter templates."""
        return [
            {
                "type": key,
                "name": value["name"],
                "description": value["description"],
                "required_fields": value["required_fields"],
            }
            for key, value in cls.LETTER_TEMPLATES.items()
        ]

    @classmethod
    def get_template_fields(cls, template_type: str) -> Dict[str, Any]:
        """Get all fields for a specific template."""
        if template_type not in cls.LETTER_TEMPLATES:
            return {"error": f"Unknown template type: {template_type}"}

        template = cls.LETTER_TEMPLATES[template_type]

        # Define all possible fields for each template
        all_fields = {
            "support_general": [
                {"name": "organization_name", "label": "Your Organization Name", "required": True},
                {"name": "organization_address", "label": "Your Organization Address", "required": False},
                {"name": "city_state_zip", "label": "City, State ZIP", "required": False},
                {"name": "project_name", "label": "Project Name", "required": True},
                {"name": "applicant_name", "label": "Applicant Organization", "required": True},
                {"name": "recipient_name", "label": "Recipient Name", "required": False},
                {"name": "relationship_description", "label": "Describe Your Relationship", "required": False, "type": "textarea"},
                {"name": "project_support_description", "label": "Why You Support This Project", "required": False, "type": "textarea"},
                {"name": "commitment_description", "label": "Your Commitment", "required": False, "type": "textarea"},
                {"name": "signatory_name", "label": "Signatory Name", "required": True},
                {"name": "signatory_title", "label": "Signatory Title", "required": True},
                {"name": "signatory_email", "label": "Signatory Email", "required": False},
                {"name": "signatory_phone", "label": "Signatory Phone", "required": False},
            ],
            "commitment_financial": [
                {"name": "organization_name", "label": "Your Organization Name", "required": True},
                {"name": "address", "label": "Address", "required": False},
                {"name": "project_name", "label": "Project Name", "required": True},
                {"name": "applicant_name", "label": "Applicant Organization", "required": True},
                {"name": "commitment_amount", "label": "Total Commitment Amount", "required": True},
                {"name": "cash_commitment", "label": "Cash Contribution Details", "required": False, "type": "textarea"},
                {"name": "inkind_commitment", "label": "In-Kind Contribution Details", "required": False, "type": "textarea"},
                {"name": "timing", "label": "When Resources Will Be Provided", "required": False},
                {"name": "conditionality", "label": "Conditions (if any)", "required": False},
                {"name": "signatory_name", "label": "Signatory Name", "required": True},
                {"name": "signatory_title", "label": "Signatory Title", "required": True},
            ],
        }

        return {
            "template_type": template_type,
            "name": template["name"],
            "description": template["description"],
            "fields": all_fields.get(template_type, [
                {"name": field, "label": field.replace("_", " ").title(), "required": True}
                for field in template["required_fields"]
            ]),
        }
