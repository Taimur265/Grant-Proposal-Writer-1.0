"""AI-powered proposal improvement service."""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class AIImprovementService:
    """Service for AI-powered proposal improvements and suggestions."""

    # Common issues and their fixes
    WRITING_ISSUES = {
        "passive_voice": {
            "pattern": r"\b(is|are|was|were|been|being)\s+(\w+ed)\b",
            "suggestion": "Consider using active voice for stronger impact",
            "severity": "low",
        },
        "weak_verbs": {
            "words": ["make", "do", "get", "have", "be", "use"],
            "suggestion": "Replace with more specific, powerful verbs",
            "severity": "medium",
        },
        "filler_words": {
            "words": ["very", "really", "actually", "basically", "just", "quite", "somewhat"],
            "suggestion": "Remove filler words for concise writing",
            "severity": "low",
        },
        "vague_language": {
            "words": ["things", "stuff", "something", "somehow", "somewhere"],
            "suggestion": "Be more specific and precise",
            "severity": "medium",
        },
    }

    # Grant writing best practices
    BEST_PRACTICES = {
        "problem_statement": [
            "Clearly define the problem being addressed",
            "Support with data and statistics",
            "Show urgency and significance",
            "Connect to broader community impact",
        ],
        "objectives": [
            "Use SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)",
            "Align objectives with funder priorities",
            "Include both short-term and long-term goals",
            "Make objectives verifiable",
        ],
        "methodology": [
            "Describe approach in clear, logical steps",
            "Justify why this approach will work",
            "Include timeline and milestones",
            "Address potential challenges and mitigation strategies",
        ],
        "evaluation": [
            "Define clear success metrics",
            "Include both quantitative and qualitative measures",
            "Describe data collection methods",
            "Plan for continuous improvement",
        ],
        "budget": [
            "Ensure all costs are justified and reasonable",
            "Align budget with proposed activities",
            "Include cost-sharing if applicable",
            "Follow funder budget guidelines",
        ],
        "sustainability": [
            "Show long-term viability beyond grant period",
            "Identify potential future funding sources",
            "Demonstrate organizational commitment",
            "Include capacity building components",
        ],
    }

    @classmethod
    def analyze_proposal(cls, content: str, sections: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Perform comprehensive proposal analysis."""
        analysis = {
            "overall_score": 0,
            "section_scores": {},
            "writing_issues": cls._find_writing_issues(content),
            "improvement_suggestions": [],
            "strengths": [],
            "weaknesses": [],
            "compliance_tips": [],
            "readability": cls._analyze_readability(content),
        }

        # Analyze each section if provided
        if sections:
            for section in sections:
                section_analysis = cls._analyze_section(
                    section.get("title", ""),
                    section.get("content", ""),
                )
                analysis["section_scores"][section.get("title", "Unknown")] = section_analysis

        # Calculate overall score
        analysis["overall_score"] = cls._calculate_overall_score(analysis)

        # Generate improvement suggestions
        analysis["improvement_suggestions"] = cls._generate_suggestions(analysis, content)

        return analysis

    @classmethod
    def _find_writing_issues(cls, content: str) -> List[Dict[str, Any]]:
        """Find writing issues in the content."""
        issues = []
        content_lower = content.lower()

        # Check for passive voice
        passive_matches = re.findall(cls.WRITING_ISSUES["passive_voice"]["pattern"], content_lower)
        if len(passive_matches) > 5:
            issues.append({
                "type": "passive_voice",
                "count": len(passive_matches),
                "suggestion": cls.WRITING_ISSUES["passive_voice"]["suggestion"],
                "severity": cls.WRITING_ISSUES["passive_voice"]["severity"],
            })

        # Check for weak verbs
        weak_verb_count = sum(content_lower.count(f" {word} ") for word in cls.WRITING_ISSUES["weak_verbs"]["words"])
        if weak_verb_count > 10:
            issues.append({
                "type": "weak_verbs",
                "count": weak_verb_count,
                "suggestion": cls.WRITING_ISSUES["weak_verbs"]["suggestion"],
                "severity": cls.WRITING_ISSUES["weak_verbs"]["severity"],
            })

        # Check for filler words
        filler_count = sum(content_lower.count(f" {word} ") for word in cls.WRITING_ISSUES["filler_words"]["words"])
        if filler_count > 5:
            issues.append({
                "type": "filler_words",
                "count": filler_count,
                "suggestion": cls.WRITING_ISSUES["filler_words"]["suggestion"],
                "severity": cls.WRITING_ISSUES["filler_words"]["severity"],
            })

        # Check for vague language
        vague_count = sum(content_lower.count(f" {word} ") for word in cls.WRITING_ISSUES["vague_language"]["words"])
        if vague_count > 3:
            issues.append({
                "type": "vague_language",
                "count": vague_count,
                "suggestion": cls.WRITING_ISSUES["vague_language"]["suggestion"],
                "severity": cls.WRITING_ISSUES["vague_language"]["severity"],
            })

        return issues

    @classmethod
    def _analyze_readability(cls, content: str) -> Dict[str, Any]:
        """Analyze content readability."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return {"score": 0, "level": "N/A", "suggestions": []}

        avg_words_per_sentence = len(words) / len(sentences)

        # Simple readability scoring
        if avg_words_per_sentence < 15:
            level = "Easy"
            score = 90
        elif avg_words_per_sentence < 20:
            level = "Moderate"
            score = 75
        elif avg_words_per_sentence < 25:
            level = "Somewhat Difficult"
            score = 60
        else:
            level = "Difficult"
            score = 40

        suggestions = []
        if avg_words_per_sentence > 20:
            suggestions.append("Consider breaking long sentences into shorter ones")
        if avg_words_per_sentence < 10:
            suggestions.append("Some sentences may be too short - consider combining related ideas")

        return {
            "score": score,
            "level": level,
            "avg_sentence_length": round(avg_words_per_sentence, 1),
            "suggestions": suggestions,
        }

    @classmethod
    def _analyze_section(cls, title: str, content: str) -> Dict[str, Any]:
        """Analyze a specific section."""
        title_lower = title.lower()
        analysis = {
            "score": 70,  # Base score
            "issues": [],
            "suggestions": [],
        }

        # Check section length
        word_count = len(content.split())
        if word_count < 100:
            analysis["issues"].append("Section may be too brief")
            analysis["score"] -= 10
        elif word_count > 2000:
            analysis["issues"].append("Section may be too long - consider condensing")
            analysis["score"] -= 5

        # Section-specific analysis
        if "problem" in title_lower or "need" in title_lower:
            if not re.search(r'\d', content):
                analysis["suggestions"].append("Add statistics or data to support the problem statement")
                analysis["score"] -= 5

        if "objective" in title_lower or "goal" in title_lower:
            smart_indicators = ["specific", "measurable", "achieve", "relevant", "time"]
            found = sum(1 for ind in smart_indicators if ind in content.lower())
            if found < 3:
                analysis["suggestions"].append("Ensure objectives follow SMART criteria")
                analysis["score"] -= 10

        if "method" in title_lower or "approach" in title_lower:
            if "timeline" not in content.lower() and "schedule" not in content.lower():
                analysis["suggestions"].append("Include a timeline for implementation")
                analysis["score"] -= 5

        if "evaluation" in title_lower:
            if "metric" not in content.lower() and "measure" not in content.lower():
                analysis["suggestions"].append("Define specific success metrics")
                analysis["score"] -= 10

        if "budget" in title_lower:
            if "justif" not in content.lower():
                analysis["suggestions"].append("Include budget justifications")
                analysis["score"] -= 5

        return analysis

    @classmethod
    def _calculate_overall_score(cls, analysis: Dict[str, Any]) -> int:
        """Calculate overall proposal score."""
        base_score = 70

        # Deduct for writing issues
        issue_penalty = sum(
            5 if issue["severity"] == "high" else 3 if issue["severity"] == "medium" else 1
            for issue in analysis["writing_issues"]
        )
        base_score -= min(issue_penalty, 20)

        # Add readability bonus
        if analysis["readability"]["score"] >= 80:
            base_score += 5

        # Consider section scores
        if analysis["section_scores"]:
            avg_section_score = sum(s["score"] for s in analysis["section_scores"].values()) / len(analysis["section_scores"])
            base_score = (base_score + avg_section_score) / 2

        return max(0, min(100, int(base_score)))

    @classmethod
    def _generate_suggestions(cls, analysis: Dict[str, Any], content: str) -> List[Dict[str, Any]]:
        """Generate improvement suggestions."""
        suggestions = []

        # Based on writing issues
        for issue in analysis["writing_issues"]:
            suggestions.append({
                "category": "writing",
                "priority": "high" if issue["severity"] == "high" else "medium",
                "title": f"Improve {issue['type'].replace('_', ' ')}",
                "description": issue["suggestion"],
                "impact": "Improves clarity and professionalism",
            })

        # Based on section analysis
        for section_name, section_data in analysis.get("section_scores", {}).items():
            for suggestion in section_data.get("suggestions", []):
                suggestions.append({
                    "category": "content",
                    "priority": "high",
                    "title": f"Enhance {section_name}",
                    "description": suggestion,
                    "impact": "Strengthens proposal competitiveness",
                })

        # General grant writing suggestions
        content_lower = content.lower()

        if "outcome" not in content_lower and "impact" not in content_lower:
            suggestions.append({
                "category": "content",
                "priority": "high",
                "title": "Add expected outcomes",
                "description": "Clearly articulate expected outcomes and long-term impact",
                "impact": "Demonstrates project value to funders",
            })

        if "sustain" not in content_lower:
            suggestions.append({
                "category": "content",
                "priority": "medium",
                "title": "Address sustainability",
                "description": "Explain how the project will continue after the grant period",
                "impact": "Shows long-term thinking and planning",
            })

        if "partner" not in content_lower and "collaborat" not in content_lower:
            suggestions.append({
                "category": "content",
                "priority": "low",
                "title": "Consider partnerships",
                "description": "Mention any partnerships or collaborations that strengthen the proposal",
                "impact": "Demonstrates community support and capacity",
            })

        return suggestions

    @classmethod
    def get_section_templates(cls, grant_type: str) -> List[Dict[str, Any]]:
        """Get recommended sections for a grant type."""
        common_sections = [
            {"name": "Executive Summary", "required": True, "recommended_words": 300},
            {"name": "Statement of Need", "required": True, "recommended_words": 500},
            {"name": "Goals and Objectives", "required": True, "recommended_words": 400},
            {"name": "Methods/Approach", "required": True, "recommended_words": 800},
            {"name": "Evaluation Plan", "required": True, "recommended_words": 400},
            {"name": "Budget and Justification", "required": True, "recommended_words": 500},
            {"name": "Organizational Capacity", "required": True, "recommended_words": 400},
            {"name": "Sustainability Plan", "required": False, "recommended_words": 300},
        ]

        if grant_type == "federal":
            common_sections.extend([
                {"name": "Specific Aims", "required": True, "recommended_words": 500},
                {"name": "Research Strategy", "required": True, "recommended_words": 1200},
                {"name": "Facilities and Resources", "required": True, "recommended_words": 300},
            ])
        elif grant_type == "research":
            common_sections.extend([
                {"name": "Literature Review", "required": True, "recommended_words": 600},
                {"name": "Research Design", "required": True, "recommended_words": 800},
                {"name": "Data Management Plan", "required": True, "recommended_words": 300},
            ])

        return common_sections

    @classmethod
    def generate_writing_tips(cls, section_type: str) -> List[str]:
        """Generate writing tips for a specific section."""
        return cls.BEST_PRACTICES.get(section_type.lower(), [
            "Be clear and concise",
            "Use specific examples",
            "Support claims with evidence",
            "Follow funder guidelines",
        ])
