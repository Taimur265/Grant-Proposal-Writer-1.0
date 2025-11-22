"""Advanced document analysis service."""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter


class DocumentAnalysisService:
    """Service for advanced document analysis and extraction."""

    # Common grant-related keywords by category
    KEYWORD_CATEGORIES = {
        "eligibility": [
            "eligible", "eligibility", "qualify", "qualification", "requirements",
            "criteria", "applicant", "organization type", "non-profit", "501(c)(3)",
        ],
        "budget": [
            "budget", "funding", "grant amount", "maximum award", "cost",
            "indirect costs", "overhead", "F&A", "matching", "cost share",
        ],
        "timeline": [
            "deadline", "due date", "submission", "timeline", "period",
            "duration", "start date", "end date", "project period",
        ],
        "requirements": [
            "required", "must", "shall", "mandatory", "necessary",
            "submit", "provide", "include", "attach", "format",
        ],
        "evaluation": [
            "evaluation", "criteria", "scoring", "review", "points",
            "weight", "merit", "assessment", "selection",
        ],
        "deliverables": [
            "deliverables", "outcomes", "outputs", "milestones", "objectives",
            "goals", "targets", "indicators", "metrics",
        ],
    }

    @classmethod
    def analyze_document(cls, content: str, document_type: str = "general") -> Dict[str, Any]:
        """Perform comprehensive document analysis."""
        analysis = {
            "statistics": cls._get_text_statistics(content),
            "keywords": cls._extract_keywords(content),
            "key_phrases": cls._extract_key_phrases(content),
            "dates": cls._extract_dates(content),
            "amounts": cls._extract_amounts(content),
            "requirements": cls._extract_requirements(content),
            "sections": cls._identify_sections(content),
            "readability": cls._calculate_readability(content),
            "document_type_analysis": cls._analyze_document_type(content, document_type),
        }
        return analysis

    @classmethod
    def _get_text_statistics(cls, content: str) -> Dict[str, Any]:
        """Get basic text statistics."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = content.split('\n\n')

        return {
            "character_count": len(content),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "avg_word_length": sum(len(w) for w in words) / max(len(words), 1),
            "avg_sentence_length": len(words) / max(len([s for s in sentences if s.strip()]), 1),
        }

    @classmethod
    def _extract_keywords(cls, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract keywords by category."""
        content_lower = content.lower()
        found_keywords = {}

        for category, keywords in cls.KEYWORD_CATEGORIES.items():
            matches = []
            for keyword in keywords:
                count = content_lower.count(keyword.lower())
                if count > 0:
                    # Find context around keyword
                    pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    contexts = re.findall(pattern, content_lower, re.IGNORECASE)
                    matches.append({
                        "keyword": keyword,
                        "count": count,
                        "contexts": contexts[:3],  # Limit to 3 contexts
                    })
            if matches:
                found_keywords[category] = sorted(matches, key=lambda x: x["count"], reverse=True)

        return found_keywords

    @classmethod
    def _extract_key_phrases(cls, content: str) -> List[Dict[str, Any]]:
        """Extract important phrases from the document."""
        # Simple n-gram extraction for key phrases
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

        # Get bigrams and trigrams
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]

        # Count frequencies
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)

        # Filter common stop phrases and get top phrases
        stop_phrases = {'the', 'and', 'for', 'that', 'with', 'this', 'from', 'will', 'are', 'have'}

        key_phrases = []
        for phrase, count in bigram_counts.most_common(20):
            if not any(stop in phrase.split() for stop in stop_phrases if len(stop) < 4):
                if count >= 2:
                    key_phrases.append({"phrase": phrase, "count": count, "type": "bigram"})

        for phrase, count in trigram_counts.most_common(15):
            words_in_phrase = phrase.split()
            if len([w for w in words_in_phrase if w not in stop_phrases]) >= 2:
                if count >= 2:
                    key_phrases.append({"phrase": phrase, "count": count, "type": "trigram"})

        return sorted(key_phrases, key=lambda x: x["count"], reverse=True)[:20]

    @classmethod
    def _extract_dates(cls, content: str) -> List[Dict[str, Any]]:
        """Extract dates from document."""
        date_patterns = [
            # Month DD, YYYY
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', 'month_day_year'),
            # MM/DD/YYYY or MM-DD-YYYY
            (r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', 'numeric'),
            # YYYY-MM-DD
            (r'\b\d{4}-\d{2}-\d{2}\b', 'iso'),
        ]

        dates = []
        for pattern, date_type in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                dates.append({
                    "date": match.group(),
                    "type": date_type,
                    "context": context,
                    "position": match.start(),
                })

        return dates

    @classmethod
    def _extract_amounts(cls, content: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from document."""
        amount_patterns = [
            # $X,XXX,XXX or $X.XX
            (r'\$[\d,]+(?:\.\d{2})?', 'usd'),
            # X dollars/USD
            (r'\b[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD)\b', 'usd_text'),
            # X million/billion
            (r'\b[\d.]+\s*(?:million|billion)\b', 'large_amount'),
        ]

        amounts = []
        for pattern, amount_type in amount_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                amounts.append({
                    "amount": match.group(),
                    "type": amount_type,
                    "context": context,
                    "position": match.start(),
                })

        return amounts

    @classmethod
    def _extract_requirements(cls, content: str) -> List[Dict[str, Any]]:
        """Extract requirements and mandatory items."""
        requirement_patterns = [
            r'(?:must|shall|required to|need to|have to)\s+([^.]+\.)',
            r'(?:applicants?|organizations?|grantees?)\s+(?:must|shall|are required to)\s+([^.]+\.)',
            r'(?:mandatory|required)\s+(?:documents?|items?|elements?):\s*([^.]+\.)',
        ]

        requirements = []
        seen = set()

        for pattern in requirement_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                req_text = match.group().strip()
                if req_text not in seen and len(req_text) > 20:
                    seen.add(req_text)
                    requirements.append({
                        "requirement": req_text,
                        "position": match.start(),
                    })

        return requirements[:20]  # Limit to 20 requirements

    @classmethod
    def _identify_sections(cls, content: str) -> List[Dict[str, Any]]:
        """Identify document sections based on headers."""
        # Common section header patterns
        header_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+):?\s*$',  # ALL CAPS headers
            r'^(\d+\.?\s+[A-Z][^.]+)$',  # Numbered sections
            r'^([IVXLC]+\.?\s+[A-Z][^.]+)$',  # Roman numeral sections
        ]

        sections = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            for pattern in header_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    # Get preview of section content
                    preview_lines = []
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if lines[j].strip():
                            preview_lines.append(lines[j].strip())

                    sections.append({
                        "title": match.group(1).strip() if match.groups() else line,
                        "line_number": i + 1,
                        "preview": ' '.join(preview_lines)[:200],
                    })
                    break

        return sections

    @classmethod
    def _calculate_readability(cls, content: str) -> Dict[str, Any]:
        """Calculate readability metrics."""
        words = content.split()
        sentences = [s for s in re.split(r'[.!?]+', content) if s.strip()]

        if not words or not sentences:
            return {"error": "Insufficient content for readability analysis"}

        # Count syllables (simplified)
        def count_syllables(word):
            word = word.lower()
            vowels = 'aeiou'
            count = 0
            prev_vowel = False
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            return max(count, 1)

        total_syllables = sum(count_syllables(w) for w in words)
        avg_syllables_per_word = total_syllables / len(words)
        avg_words_per_sentence = len(words) / len(sentences)

        # Flesch Reading Ease
        flesch_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))

        # Determine reading level
        if flesch_score >= 90:
            level = "Very Easy (5th grade)"
        elif flesch_score >= 80:
            level = "Easy (6th grade)"
        elif flesch_score >= 70:
            level = "Fairly Easy (7th grade)"
        elif flesch_score >= 60:
            level = "Standard (8th-9th grade)"
        elif flesch_score >= 50:
            level = "Fairly Difficult (10th-12th grade)"
        elif flesch_score >= 30:
            level = "Difficult (College)"
        else:
            level = "Very Difficult (Professional)"

        return {
            "flesch_reading_ease": round(flesch_score, 1),
            "reading_level": level,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        }

    @classmethod
    def _analyze_document_type(cls, content: str, document_type: str) -> Dict[str, Any]:
        """Perform analysis specific to document type."""
        content_lower = content.lower()

        if document_type in ["guidelines", "rfp", "tor"]:
            return cls._analyze_guidelines_document(content_lower)
        elif document_type in ["organization_profile", "beneficiary"]:
            return cls._analyze_beneficiary_document(content_lower)
        elif document_type == "budget_template":
            return cls._analyze_budget_document(content_lower)
        else:
            return {"type": "general", "analysis": "Standard document analysis applied"}

    @classmethod
    def _analyze_guidelines_document(cls, content: str) -> Dict[str, Any]:
        """Analyze guidelines/RFP document."""
        analysis = {
            "type": "guidelines",
            "has_eligibility_section": bool(re.search(r'eligib', content)),
            "has_budget_section": bool(re.search(r'budget|funding', content)),
            "has_timeline_section": bool(re.search(r'timeline|deadline|due date', content)),
            "has_evaluation_criteria": bool(re.search(r'evaluation|criteria|scoring', content)),
            "has_submission_requirements": bool(re.search(r'submission|submit|format', content)),
            "compliance_items": [],
        }

        # Extract specific compliance items
        compliance_patterns = [
            (r'page limit[:\s]+(\d+)', "Page limit"),
            (r'word limit[:\s]+(\d+)', "Word limit"),
            (r'font[:\s]+([^\n,]+)', "Font requirement"),
            (r'margin[:\s]+([^\n,]+)', "Margin requirement"),
            (r'file format[:\s]+([^\n,]+)', "File format"),
        ]

        for pattern, item_type in compliance_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                analysis["compliance_items"].append({
                    "type": item_type,
                    "value": match.group(1).strip(),
                })

        return analysis

    @classmethod
    def _analyze_beneficiary_document(cls, content: str) -> Dict[str, Any]:
        """Analyze beneficiary/organization document."""
        analysis = {
            "type": "beneficiary",
            "has_mission_statement": bool(re.search(r'mission|purpose|vision', content)),
            "has_organizational_info": bool(re.search(r'founded|established|incorporated', content)),
            "has_financial_info": bool(re.search(r'revenue|budget|assets|financial', content)),
            "has_team_info": bool(re.search(r'team|staff|personnel|employees', content)),
            "has_past_projects": bool(re.search(r'past project|previous|track record|experience', content)),
            "organization_indicators": [],
        }

        # Look for organization type indicators
        org_types = [
            ("501(c)(3)", "US Nonprofit"),
            ("non-profit", "Nonprofit"),
            ("ngo", "NGO"),
            ("cbo", "Community-Based Organization"),
            ("university", "Academic Institution"),
            ("government", "Government Entity"),
        ]

        for pattern, org_type in org_types:
            if pattern in content:
                analysis["organization_indicators"].append(org_type)

        return analysis

    @classmethod
    def _analyze_budget_document(cls, content: str) -> Dict[str, Any]:
        """Analyze budget document."""
        return {
            "type": "budget",
            "has_personnel_section": bool(re.search(r'personnel|salary|wage', content)),
            "has_equipment_section": bool(re.search(r'equipment', content)),
            "has_travel_section": bool(re.search(r'travel', content)),
            "has_indirect_costs": bool(re.search(r'indirect|overhead|f&a', content)),
            "has_cost_share": bool(re.search(r'cost share|matching|in-kind', content)),
        }

    @classmethod
    def compare_documents(
        cls,
        doc1_content: str,
        doc2_content: str,
        doc1_name: str = "Document 1",
        doc2_name: str = "Document 2",
    ) -> Dict[str, Any]:
        """Compare two documents for similarities and differences."""
        # Get word sets
        words1 = set(re.findall(r'\b[a-zA-Z]{3,}\b', doc1_content.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]{3,}\b', doc2_content.lower()))

        # Calculate similarity
        intersection = words1 & words2
        union = words1 | words2
        jaccard_similarity = len(intersection) / max(len(union), 1)

        # Get unique words
        unique_to_doc1 = words1 - words2
        unique_to_doc2 = words2 - words1

        # Get statistics
        stats1 = cls._get_text_statistics(doc1_content)
        stats2 = cls._get_text_statistics(doc2_content)

        return {
            "similarity_score": round(jaccard_similarity * 100, 1),
            "common_words_count": len(intersection),
            "unique_to": {
                doc1_name: list(unique_to_doc1)[:50],
                doc2_name: list(unique_to_doc2)[:50],
            },
            "statistics_comparison": {
                doc1_name: stats1,
                doc2_name: stats2,
            },
        }


class RequirementsExtractor:
    """Extract and organize requirements from grant documents."""

    @classmethod
    def extract_all_requirements(cls, content: str) -> Dict[str, List[str]]:
        """Extract all requirements organized by category."""
        requirements = {
            "eligibility": [],
            "submission": [],
            "formatting": [],
            "content": [],
            "budget": [],
            "timeline": [],
            "reporting": [],
        }

        # Eligibility requirements
        eligibility_patterns = [
            r'eligible\s+(?:applicants?|organizations?)\s+(?:include|are|must)[:\s]+([^.]+\.)',
            r'to\s+be\s+eligible[,:\s]+([^.]+\.)',
            r'eligibility\s+(?:requirements?|criteria)[:\s]+([^.]+\.)',
        ]

        for pattern in eligibility_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            requirements["eligibility"].extend(matches)

        # Submission requirements
        submission_patterns = [
            r'submit(?:ted)?\s+(?:by|via|through|to)[:\s]+([^.]+\.)',
            r'submission\s+(?:must|should|shall)[:\s]+([^.]+\.)',
            r'applications?\s+must\s+be\s+(?:submitted|received)[:\s]+([^.]+\.)',
        ]

        for pattern in submission_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            requirements["submission"].extend(matches)

        # Formatting requirements
        formatting_patterns = [
            r'(?:format|formatting)\s+requirements?[:\s]+([^.]+\.)',
            r'(?:font|margin|spacing|page)\s+(?:size|requirement|limit)[:\s]+([^.]+\.)',
            r'(?:must|should)\s+be\s+(?:formatted|typed|written)\s+([^.]+\.)',
        ]

        for pattern in formatting_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            requirements["formatting"].extend(matches)

        # Clean up and deduplicate
        for category in requirements:
            requirements[category] = list(set([
                req.strip() for req in requirements[category]
                if len(req.strip()) > 20
            ]))[:10]

        return requirements
