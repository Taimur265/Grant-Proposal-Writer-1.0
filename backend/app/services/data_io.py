"""Data import/export utilities."""

import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID


class DataExporter:
    """Service for exporting data to various formats."""

    @staticmethod
    def to_json(data: Any, pretty: bool = True) -> str:
        """Export data to JSON string."""
        def serialize(obj):
            if isinstance(obj, UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        if pretty:
            return json.dumps(data, default=serialize, indent=2)
        return json.dumps(data, default=serialize)

    @staticmethod
    def to_csv(data: List[Dict], columns: Optional[List[str]] = None) -> str:
        """Export list of dictionaries to CSV string."""
        if not data:
            return ""

        output = io.StringIO()

        # Determine columns
        if columns:
            fieldnames = columns
        else:
            fieldnames = list(data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for row in data:
            # Convert non-string values
            processed_row = {}
            for key, value in row.items():
                if key in fieldnames:
                    if isinstance(value, (list, dict)):
                        processed_row[key] = json.dumps(value)
                    elif isinstance(value, datetime):
                        processed_row[key] = value.isoformat()
                    elif isinstance(value, UUID):
                        processed_row[key] = str(value)
                    else:
                        processed_row[key] = value
            writer.writerow(processed_row)

        return output.getvalue()

    @staticmethod
    def proposals_to_export(proposals: List[Dict]) -> List[Dict]:
        """Format proposals for export."""
        export_data = []
        for proposal in proposals:
            export_data.append({
                "title": proposal.get("title"),
                "status": proposal.get("status"),
                "created_at": proposal.get("created_at"),
                "updated_at": proposal.get("updated_at"),
                "word_count": len(proposal.get("content", "").split()) if proposal.get("content") else 0,
                "sections_count": len(proposal.get("sections", [])),
            })
        return export_data

    @staticmethod
    def budget_to_export(budget: Dict) -> Dict:
        """Format budget for export."""
        return {
            "personnel": budget.get("personnel", []),
            "equipment": budget.get("equipment", []),
            "supplies": budget.get("supplies", []),
            "travel": budget.get("travel", []),
            "other": budget.get("other", []),
            "indirect": budget.get("indirect", {}),
            "totals": budget.get("totals", {}),
            "summary": {
                "total_direct": budget.get("totals", {}).get("direct", 0),
                "total_indirect": budget.get("totals", {}).get("indirect", 0),
                "grand_total": budget.get("totals", {}).get("total", 0),
            },
        }

    @staticmethod
    def analytics_to_export(analytics: Dict) -> Dict:
        """Format analytics for export."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": analytics,
        }


class DataImporter:
    """Service for importing data from various formats."""

    @staticmethod
    def from_json(json_string: str) -> Any:
        """Parse JSON string to Python object."""
        return json.loads(json_string)

    @staticmethod
    def from_csv(csv_string: str, has_header: bool = True) -> List[Dict]:
        """Parse CSV string to list of dictionaries."""
        input_stream = io.StringIO(csv_string)

        if has_header:
            reader = csv.DictReader(input_stream)
            return list(reader)
        else:
            reader = csv.reader(input_stream)
            rows = list(reader)
            if not rows:
                return []
            # Use column indices as keys
            return [
                {f"col_{i}": value for i, value in enumerate(row)}
                for row in rows
            ]

    @staticmethod
    def validate_proposal_import(data: Dict) -> Dict[str, Any]:
        """Validate proposal import data."""
        errors = []
        warnings = []

        if not data.get("title"):
            errors.append("Title is required")

        if not data.get("content") and not data.get("sections"):
            warnings.append("No content or sections provided")

        if data.get("sections"):
            for i, section in enumerate(data["sections"]):
                if not section.get("title"):
                    errors.append(f"Section {i+1} missing title")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data,
        }

    @staticmethod
    def validate_budget_import(data: Dict) -> Dict[str, Any]:
        """Validate budget import data."""
        errors = []
        warnings = []

        required_categories = ["personnel", "equipment", "supplies", "travel", "other"]
        for category in required_categories:
            if category not in data:
                warnings.append(f"Missing category: {category}")
            elif not isinstance(data[category], list):
                errors.append(f"Category {category} must be a list")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data,
        }

    @staticmethod
    def parse_budget_csv(csv_string: str) -> Dict[str, List[Dict]]:
        """Parse budget from CSV format."""
        rows = DataImporter.from_csv(csv_string)

        budget = {
            "personnel": [],
            "equipment": [],
            "supplies": [],
            "travel": [],
            "other": [],
        }

        for row in rows:
            category = row.get("category", "other").lower()
            if category not in budget:
                category = "other"

            item = {
                "description": row.get("description", row.get("item", "")),
                "amount": float(row.get("amount", 0)),
                "quantity": int(row.get("quantity", 1)),
                "unit_cost": float(row.get("unit_cost", row.get("amount", 0))),
                "justification": row.get("justification", row.get("notes", "")),
            }
            budget[category].append(item)

        return budget


class ProjectBackup:
    """Service for creating and restoring project backups."""

    @staticmethod
    def create_backup(project_data: Dict) -> Dict:
        """Create a complete project backup."""
        return {
            "backup_version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "project": {
                "name": project_data.get("name"),
                "description": project_data.get("description"),
                "status": project_data.get("status"),
                "funder_name": project_data.get("funder_name"),
                "deadline": project_data.get("deadline"),
                "target_amount": project_data.get("target_amount"),
            },
            "proposals": project_data.get("proposals", []),
            "documents": [
                {
                    "original_filename": doc.get("original_filename"),
                    "document_type": doc.get("document_type"),
                    "category": doc.get("category"),
                    "extracted_text": doc.get("extracted_text"),
                }
                for doc in project_data.get("documents", [])
            ],
            "budget": project_data.get("budget"),
            "timeline": project_data.get("timeline"),
            "comments": project_data.get("comments", []),
        }

    @staticmethod
    def validate_backup(backup_data: Dict) -> Dict[str, Any]:
        """Validate backup data before restore."""
        errors = []
        warnings = []

        if backup_data.get("backup_version") != "1.0":
            warnings.append("Backup version mismatch, some data may not import correctly")

        if not backup_data.get("project"):
            errors.append("Missing project data")

        if not backup_data.get("project", {}).get("name"):
            errors.append("Project name is required")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def restore_preview(backup_data: Dict) -> Dict:
        """Generate preview of what will be restored."""
        return {
            "project_name": backup_data.get("project", {}).get("name"),
            "proposals_count": len(backup_data.get("proposals", [])),
            "documents_count": len(backup_data.get("documents", [])),
            "has_budget": backup_data.get("budget") is not None,
            "has_timeline": backup_data.get("timeline") is not None,
            "comments_count": len(backup_data.get("comments", [])),
            "backup_date": backup_data.get("created_at"),
        }
