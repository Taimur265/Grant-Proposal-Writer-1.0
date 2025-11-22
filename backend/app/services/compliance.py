"""Compliance checking service for grant proposals."""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class ComplianceChecker:
    """Service for checking proposal compliance against guidelines."""

    # Standard compliance categories
    COMPLIANCE_CATEGORIES = {
        "formatting": {
            "name": "Formatting Requirements",
            "weight": 15,
            "checks": [
                "page_limit",
                "font_requirements",
                "margin_requirements",
                "spacing_requirements",
                "file_format",
            ],
        },
        "content": {
            "name": "Required Content",
            "weight": 30,
            "checks": [
                "required_sections",
                "executive_summary",
                "problem_statement",
                "objectives",
                "methodology",
                "evaluation_plan",
                "budget_narrative",
            ],
        },
        "eligibility": {
            "name": "Eligibility Criteria",
            "weight": 25,
            "checks": [
                "organization_type",
                "geographic_eligibility",
                "funding_history",
                "registration_status",
            ],
        },
        "budget": {
            "name": "Budget Compliance",
            "weight": 20,
            "checks": [
                "budget_ceiling",
                "indirect_rate",
                "cost_sharing",
                "allowable_costs",
                "budget_justification",
            ],
        },
        "submission": {
            "name": "Submission Requirements",
            "weight": 10,
            "checks": [
                "deadline",
                "required_attachments",
                "signature_requirements",
                "submission_method",
            ],
        },
    }

    @classmethod
    def check_compliance(
        cls,
        proposal_content: str,
        guidelines_content: str,
        budget_data: Optional[Dict] = None,
        organization_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Perform comprehensive compliance check."""
        results = {
            "overall_score": 0,
            "category_scores": {},
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "recommendations": [],
            "details": {},
        }

        # Extract requirements from guidelines
        requirements = cls._extract_requirements(guidelines_content)

        # Check each category
        for category_id, category_info in cls.COMPLIANCE_CATEGORIES.items():
            category_result = cls._check_category(
                category_id,
                category_info,
                proposal_content,
                requirements,
                budget_data,
                organization_data,
            )
            results["category_scores"][category_id] = category_result
            results["passed_checks"].extend(category_result["passed"])
            results["failed_checks"].extend(category_result["failed"])
            results["warnings"].extend(category_result["warnings"])

        # Calculate overall score
        total_weight = sum(cat["weight"] for cat in cls.COMPLIANCE_CATEGORIES.values())
        weighted_score = sum(
            results["category_scores"][cat_id]["score"] * cls.COMPLIANCE_CATEGORIES[cat_id]["weight"]
            for cat_id in cls.COMPLIANCE_CATEGORIES
        )
        results["overall_score"] = round(weighted_score / total_weight, 1)

        # Generate recommendations
        results["recommendations"] = cls._generate_recommendations(results)

        return results

    @classmethod
    def _extract_requirements(cls, guidelines_content: str) -> Dict[str, Any]:
        """Extract requirements from guidelines text."""
        requirements = {
            "page_limit": None,
            "word_limit": None,
            "font_size": None,
            "font_family": None,
            "margins": None,
            "line_spacing": None,
            "max_budget": None,
            "max_indirect_rate": None,
            "required_sections": [],
            "required_attachments": [],
            "deadline": None,
            "eligible_organizations": [],
        }

        content_lower = guidelines_content.lower()

        # Extract page limit
        page_match = re.search(r'(?:page\s*limit|maximum\s*pages?)[:\s]+(\d+)', content_lower)
        if page_match:
            requirements["page_limit"] = int(page_match.group(1))

        # Extract word limit
        word_match = re.search(r'(?:word\s*limit|maximum\s*words?)[:\s]+(\d+)', content_lower)
        if word_match:
            requirements["word_limit"] = int(word_match.group(1))

        # Extract font requirements
        font_match = re.search(r'font[:\s]+(\d+)\s*(?:pt|point)', content_lower)
        if font_match:
            requirements["font_size"] = int(font_match.group(1))

        # Extract margin requirements
        margin_match = re.search(r'margins?[:\s]+(\d+(?:\.\d+)?)\s*(?:inch|in|")', content_lower)
        if margin_match:
            requirements["margins"] = float(margin_match.group(1))

        # Extract budget limit
        budget_match = re.search(r'(?:maximum\s*(?:award|budget|funding)|up\s*to)[:\s]*\$?([\d,]+)', content_lower)
        if budget_match:
            requirements["max_budget"] = float(budget_match.group(1).replace(',', ''))

        # Extract indirect rate limit
        indirect_match = re.search(r'indirect\s*(?:cost\s*)?rate[:\s]*(?:up\s*to\s*)?(\d+(?:\.\d+)?)\s*%', content_lower)
        if indirect_match:
            requirements["max_indirect_rate"] = float(indirect_match.group(1)) / 100

        # Identify required sections
        section_patterns = [
            (r'executive\s*summary', 'Executive Summary'),
            (r'(?:problem|need)\s*statement', 'Problem Statement'),
            (r'(?:goals?|objectives?)', 'Goals and Objectives'),
            (r'(?:methodology|approach|methods?)', 'Methodology'),
            (r'evaluation\s*(?:plan)?', 'Evaluation Plan'),
            (r'budget\s*(?:narrative|justification)', 'Budget Narrative'),
            (r'timeline', 'Timeline'),
            (r'sustainability', 'Sustainability Plan'),
            (r'organizational?\s*(?:capacity|background)', 'Organizational Capacity'),
        ]

        for pattern, section_name in section_patterns:
            if re.search(pattern, content_lower):
                requirements["required_sections"].append(section_name)

        return requirements

    @classmethod
    def _check_category(
        cls,
        category_id: str,
        category_info: Dict,
        proposal_content: str,
        requirements: Dict,
        budget_data: Optional[Dict],
        organization_data: Optional[Dict],
    ) -> Dict[str, Any]:
        """Check compliance for a specific category."""
        result = {
            "name": category_info["name"],
            "score": 100,
            "passed": [],
            "failed": [],
            "warnings": [],
        }

        proposal_lower = proposal_content.lower()
        word_count = len(proposal_content.split())

        if category_id == "formatting":
            # Check word limit
            if requirements.get("word_limit"):
                if word_count <= requirements["word_limit"]:
                    result["passed"].append({
                        "check": "word_limit",
                        "message": f"Word count ({word_count}) within limit ({requirements['word_limit']})",
                    })
                else:
                    result["failed"].append({
                        "check": "word_limit",
                        "message": f"Word count ({word_count}) exceeds limit ({requirements['word_limit']})",
                        "severity": "high",
                    })
                    result["score"] -= 30

        elif category_id == "content":
            # Check for required sections
            for section in requirements.get("required_sections", []):
                section_lower = section.lower()
                if section_lower in proposal_lower or section_lower.replace(' ', '') in proposal_lower.replace(' ', ''):
                    result["passed"].append({
                        "check": f"section_{section.lower().replace(' ', '_')}",
                        "message": f"'{section}' section found",
                    })
                else:
                    result["failed"].append({
                        "check": f"section_{section.lower().replace(' ', '_')}",
                        "message": f"'{section}' section not found or unclear",
                        "severity": "high",
                    })
                    result["score"] -= 15

            # Check for key content elements
            content_checks = [
                (r'(?:problem|need|challenge)', "Problem/need statement"),
                (r'(?:objective|goal|aim)', "Clear objectives"),
                (r'(?:method|approach|strategy)', "Methodology description"),
                (r'(?:evaluat|measure|assess)', "Evaluation approach"),
                (r'(?:outcome|impact|result)', "Expected outcomes"),
            ]

            for pattern, check_name in content_checks:
                if re.search(pattern, proposal_lower):
                    result["passed"].append({
                        "check": check_name.lower().replace(' ', '_'),
                        "message": f"{check_name} included",
                    })
                else:
                    result["warnings"].append({
                        "check": check_name.lower().replace(' ', '_'),
                        "message": f"{check_name} may be missing or unclear",
                    })

        elif category_id == "budget" and budget_data:
            # Check budget ceiling
            if requirements.get("max_budget") and budget_data.get("total"):
                if budget_data["total"] <= requirements["max_budget"]:
                    result["passed"].append({
                        "check": "budget_ceiling",
                        "message": f"Total budget (${budget_data['total']:,.2f}) within limit",
                    })
                else:
                    result["failed"].append({
                        "check": "budget_ceiling",
                        "message": f"Total budget exceeds maximum of ${requirements['max_budget']:,.2f}",
                        "severity": "critical",
                    })
                    result["score"] -= 50

            # Check indirect rate
            if requirements.get("max_indirect_rate") and budget_data.get("indirect_rate"):
                if budget_data["indirect_rate"] <= requirements["max_indirect_rate"]:
                    result["passed"].append({
                        "check": "indirect_rate",
                        "message": f"Indirect rate ({budget_data['indirect_rate']*100:.1f}%) within limit",
                    })
                else:
                    result["failed"].append({
                        "check": "indirect_rate",
                        "message": f"Indirect rate exceeds maximum of {requirements['max_indirect_rate']*100:.1f}%",
                        "severity": "high",
                    })
                    result["score"] -= 25

        elif category_id == "eligibility" and organization_data:
            # Check organization eligibility
            eligible_types = requirements.get("eligible_organizations", [])
            org_type = organization_data.get("organization_type", "").lower()

            if not eligible_types or any(t.lower() in org_type for t in eligible_types):
                result["passed"].append({
                    "check": "organization_type",
                    "message": "Organization type appears eligible",
                })
            else:
                result["warnings"].append({
                    "check": "organization_type",
                    "message": "Verify organization eligibility requirements",
                })

        # Ensure score doesn't go below 0
        result["score"] = max(0, result["score"])

        return result

    @classmethod
    def _generate_recommendations(cls, results: Dict) -> List[Dict[str, Any]]:
        """Generate recommendations based on compliance results."""
        recommendations = []

        # High priority: Failed checks
        for check in results["failed_checks"]:
            severity = check.get("severity", "medium")
            recommendations.append({
                "priority": "high" if severity in ["high", "critical"] else "medium",
                "category": "compliance",
                "title": f"Address: {check['message']}",
                "description": f"This issue must be resolved before submission.",
                "action": "required",
            })

        # Medium priority: Warnings
        for warning in results["warnings"]:
            recommendations.append({
                "priority": "medium",
                "category": "improvement",
                "title": f"Review: {warning['message']}",
                "description": "Consider addressing this to strengthen your proposal.",
                "action": "recommended",
            })

        # General recommendations based on score
        if results["overall_score"] < 60:
            recommendations.append({
                "priority": "high",
                "category": "general",
                "title": "Significant compliance issues detected",
                "description": "Multiple areas need attention before submission. Review all failed checks carefully.",
                "action": "required",
            })
        elif results["overall_score"] < 80:
            recommendations.append({
                "priority": "medium",
                "category": "general",
                "title": "Some compliance improvements needed",
                "description": "Address remaining issues to improve competitiveness.",
                "action": "recommended",
            })
        else:
            recommendations.append({
                "priority": "low",
                "category": "general",
                "title": "Good compliance status",
                "description": "Most requirements are met. Final review recommended before submission.",
                "action": "optional",
            })

        return recommendations

    @classmethod
    def quick_check(cls, proposal_content: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quick compliance check with provided requirements."""
        results = {
            "compliant": True,
            "issues": [],
            "word_count": len(proposal_content.split()),
        }

        # Check word limit
        if requirements.get("word_limit"):
            if results["word_count"] > requirements["word_limit"]:
                results["compliant"] = False
                results["issues"].append(f"Word count ({results['word_count']}) exceeds limit ({requirements['word_limit']})")

        # Check for required keywords/sections
        for section in requirements.get("required_sections", []):
            if section.lower() not in proposal_content.lower():
                results["issues"].append(f"Required section '{section}' not found")

        return results
