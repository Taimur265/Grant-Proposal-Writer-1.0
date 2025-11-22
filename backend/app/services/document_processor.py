"""Document processing service for extracting text from various file formats."""

import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio

import chardet
from docx import Document as DocxDocument
from pypdf2 import PdfReader
import pdfplumber
from openpyxl import load_workbook
from pptx import Presentation
import mammoth

from app.config import settings


class DocumentProcessor:
    """Service for processing and extracting content from documents."""

    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.txt': 'text',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.pptx': 'powerpoint',
        '.ppt': 'powerpoint',
        '.rtf': 'rtf',
        '.csv': 'csv',
    }

    @classmethod
    async def process_document(cls, file_path: str) -> Dict[str, Any]:
        """
        Process a document and extract its content.

        Returns:
            Dict containing extracted_text, metadata, and key_points
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Run extraction in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, cls._extract_content, file_path, file_ext
        )

        return result

    @classmethod
    def _extract_content(cls, file_path: str, file_ext: str) -> Dict[str, Any]:
        """Extract content based on file type."""
        extractors = {
            '.pdf': cls._extract_pdf,
            '.docx': cls._extract_docx,
            '.doc': cls._extract_doc,
            '.txt': cls._extract_text,
            '.xlsx': cls._extract_excel,
            '.xls': cls._extract_excel,
            '.pptx': cls._extract_powerpoint,
            '.ppt': cls._extract_powerpoint,
            '.rtf': cls._extract_rtf,
            '.csv': cls._extract_csv,
        }

        extractor = extractors.get(file_ext)
        if not extractor:
            raise ValueError(f"No extractor for {file_ext}")

        text, metadata = extractor(file_path)

        # Extract key information
        key_points = cls._extract_key_points(text)

        return {
            "extracted_text": text,
            "metadata": metadata,
            "key_points": key_points,
            "word_count": len(text.split()) if text else 0,
        }

    @staticmethod
    def _extract_pdf(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from PDF."""
        text_parts = []
        metadata = {}

        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                # Extract tables if present
                tables = []
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                if tables:
                    metadata["tables_count"] = len(tables)
        except Exception:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                metadata["page_count"] = len(reader.pages)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                # Extract PDF metadata
                if reader.metadata:
                    metadata["title"] = reader.metadata.get("/Title", "")
                    metadata["author"] = reader.metadata.get("/Author", "")
                    metadata["created"] = str(reader.metadata.get("/CreationDate", ""))

        return "\n\n".join(text_parts), metadata

    @staticmethod
    def _extract_docx(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text and metadata from DOCX."""
        doc = DocxDocument(file_path)

        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        # Extract from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells]
                text_parts.append(" | ".join(row_text))

        metadata = {
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
        }

        # Extract core properties
        if doc.core_properties:
            metadata["title"] = doc.core_properties.title or ""
            metadata["author"] = doc.core_properties.author or ""
            metadata["created"] = str(doc.core_properties.created or "")

        return "\n\n".join(text_parts), metadata

    @staticmethod
    def _extract_doc(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from DOC using mammoth."""
        with open(file_path, "rb") as f:
            result = mammoth.extract_raw_text(f)
            text = result.value

        return text, {"format": "legacy_doc"}

    @staticmethod
    def _extract_text(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from plain text files."""
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')

        with open(file_path, 'r', encoding=encoding) as f:
            text = f.read()

        return text, {"encoding": encoding}

    @staticmethod
    def _extract_excel(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from Excel files."""
        wb = load_workbook(file_path, data_only=True)

        text_parts = []
        sheet_names = []

        for sheet_name in wb.sheetnames:
            sheet_names.append(sheet_name)
            sheet = wb[sheet_name]
            text_parts.append(f"=== Sheet: {sheet_name} ===")

            for row in sheet.iter_rows():
                row_values = []
                for cell in row:
                    if cell.value is not None:
                        row_values.append(str(cell.value))
                if row_values:
                    text_parts.append(" | ".join(row_values))

        metadata = {
            "sheet_count": len(wb.sheetnames),
            "sheet_names": sheet_names,
        }

        return "\n".join(text_parts), metadata

    @staticmethod
    def _extract_powerpoint(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PowerPoint files."""
        prs = Presentation(file_path)

        text_parts = []
        slide_count = 0

        for slide in prs.slides:
            slide_count += 1
            slide_text = [f"=== Slide {slide_count} ==="]

            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            text_parts.append("\n".join(slide_text))

        metadata = {"slide_count": slide_count}

        return "\n\n".join(text_parts), metadata

    @staticmethod
    def _extract_rtf(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from RTF files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Basic RTF text extraction (removes RTF formatting)
        text = re.sub(r'\\[a-z]+\d*\s?', '', content)
        text = re.sub(r'[{}]', '', text)
        text = text.strip()

        return text, {"format": "rtf"}

    @staticmethod
    def _extract_csv(file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from CSV files."""
        import csv

        text_parts = []
        row_count = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                row_count += 1
                text_parts.append(" | ".join(row))

        metadata = {"row_count": row_count}

        return "\n".join(text_parts), metadata

    @staticmethod
    def _extract_key_points(text: str) -> List[str]:
        """Extract key points from document text."""
        if not text:
            return []

        key_points = []

        # Look for section headers
        header_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+):',  # ALL CAPS headers
            r'^\d+\.\s*([A-Z].+)$',  # Numbered sections
            r'^(?:Section|Article|Part)\s+\d+[:\.]?\s*(.+)$',  # Section markers
        ]

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in header_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    key_points.append(match.group(1).strip())
                    break

        # Look for key terms
        key_terms = [
            r'deadline[:\s]+([^.\n]+)',
            r'budget[:\s]+([^.\n]+)',
            r'eligib\w+[:\s]+([^.\n]+)',
            r'requir\w+[:\s]+([^.\n]+)',
            r'objective[s]?[:\s]+([^.\n]+)',
            r'goal[s]?[:\s]+([^.\n]+)',
        ]

        for pattern in key_terms:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_points.extend([m.strip() for m in matches[:3]])  # Limit per term

        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for point in key_points:
            if point.lower() not in seen:
                seen.add(point.lower())
                unique_points.append(point)

        return unique_points[:20]  # Limit total key points

    @classmethod
    def analyze_guidelines(cls, text: str) -> Dict[str, Any]:
        """Analyze guidelines document to extract structured requirements."""
        analysis = {
            "requirements": [],
            "eligibility_criteria": [],
            "evaluation_criteria": [],
            "deadlines": [],
            "budget_requirements": {},
            "submission_format": {},
            "sections_required": [],
        }

        # Extract requirements
        req_patterns = [
            r'(?:must|shall|required to|need to)\s+([^.]+)',
            r'applicants?\s+(?:must|shall)\s+([^.]+)',
        ]
        for pattern in req_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            analysis["requirements"].extend(matches[:10])

        # Extract eligibility criteria
        elig_section = re.search(
            r'eligib\w+[:\s]*criteria[:\s]*(.*?)(?=\n\n|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if elig_section:
            criteria = re.findall(r'[-•]\s*([^-•\n]+)', elig_section.group(1))
            analysis["eligibility_criteria"] = [c.strip() for c in criteria]

        # Extract evaluation criteria
        eval_section = re.search(
            r'evaluat\w+[:\s]*criteria[:\s]*(.*?)(?=\n\n|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if eval_section:
            criteria = re.findall(r'[-•]\s*([^-•\n]+)', eval_section.group(1))
            analysis["evaluation_criteria"] = [c.strip() for c in criteria]

        # Extract deadlines
        date_patterns = [
            r'deadline[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'due\s+(?:date|by)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            r'submit(?:ted)?\s+by[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            analysis["deadlines"].extend(matches)

        # Extract budget info
        budget_match = re.search(
            r'(?:maximum|minimum|total)\s+(?:budget|funding|award)[:\s]*\$?([\d,]+)',
            text, re.IGNORECASE
        )
        if budget_match:
            analysis["budget_requirements"]["amount"] = budget_match.group(1)

        # Extract required sections
        section_patterns = [
            r'(?:proposal|application)\s+must\s+include[:\s]*(.*?)(?=\n\n|\Z)',
            r'required\s+sections?[:\s]*(.*?)(?=\n\n|\Z)',
        ]
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections = re.findall(r'[-•\d.]\s*([^-•\n]+)', match.group(1))
                analysis["sections_required"].extend([s.strip() for s in sections])

        return analysis
