"""Budget service for grant proposal budget management."""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import json


class BudgetService:
    """Service for managing proposal budgets."""

    # Standard budget categories
    CATEGORIES = {
        "personnel": {
            "name": "Personnel",
            "description": "Salaries, wages, and fringe benefits",
            "subcategories": [
                "Principal Investigator",
                "Co-Investigators",
                "Research Staff",
                "Administrative Staff",
                "Consultants",
                "Fringe Benefits",
            ],
        },
        "equipment": {
            "name": "Equipment",
            "description": "Equipment purchases over $5,000",
            "subcategories": [
                "Laboratory Equipment",
                "Computer Hardware",
                "Software Licenses",
                "Vehicles",
                "Other Equipment",
            ],
        },
        "supplies": {
            "name": "Supplies",
            "description": "Consumable supplies and materials",
            "subcategories": [
                "Laboratory Supplies",
                "Office Supplies",
                "Field Supplies",
                "Educational Materials",
                "Other Supplies",
            ],
        },
        "travel": {
            "name": "Travel",
            "description": "Domestic and international travel",
            "subcategories": [
                "Domestic Travel",
                "International Travel",
                "Conference Registration",
                "Field Work Travel",
            ],
        },
        "contractual": {
            "name": "Contractual/Subawards",
            "description": "Subcontracts and subawards",
            "subcategories": [
                "Subawards",
                "Contracts",
                "Professional Services",
            ],
        },
        "other": {
            "name": "Other Direct Costs",
            "description": "Other allowable direct costs",
            "subcategories": [
                "Publication Costs",
                "Participant Support",
                "Communication",
                "Printing and Copying",
                "Meeting Costs",
                "Other",
            ],
        },
        "indirect": {
            "name": "Indirect Costs",
            "description": "Facilities and administrative costs",
            "subcategories": [
                "F&A Costs",
            ],
        },
    }

    @classmethod
    def get_budget_template(cls, grant_type: str = "default") -> Dict[str, Any]:
        """Get budget template based on grant type."""
        template = {
            "categories": cls.CATEGORIES,
            "settings": {
                "currency": "USD",
                "indirect_rate": 0.0,
                "indirect_base": "mtdc",  # Modified Total Direct Costs
                "exclude_from_indirect": ["equipment", "participant_support", "subawards_over_25k"],
            },
        }

        # Customize for grant types
        if grant_type == "federal":
            template["settings"]["indirect_rate"] = 0.54  # Example negotiated rate
        elif grant_type == "foundation":
            template["settings"]["indirect_rate"] = 0.15  # Many foundations cap at 15%
        elif grant_type == "corporate":
            template["settings"]["indirect_rate"] = 0.10

        return template

    @classmethod
    def calculate_budget(cls, line_items: List[Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate complete budget from line items."""
        # Group by category
        by_category = {}
        total_direct = Decimal("0")

        for item in line_items:
            category = item.get("category", "other")
            amount = Decimal(str(item.get("amount", 0)))

            if category not in by_category:
                by_category[category] = {
                    "items": [],
                    "subtotal": Decimal("0"),
                }

            by_category[category]["items"].append(item)
            by_category[category]["subtotal"] += amount
            total_direct += amount

        # Calculate indirect costs base
        indirect_base = total_direct
        exclude_categories = settings.get("exclude_from_indirect", [])
        for cat in exclude_categories:
            if cat in by_category:
                indirect_base -= by_category[cat]["subtotal"]

        # Calculate indirect costs
        indirect_rate = Decimal(str(settings.get("indirect_rate", 0)))
        indirect_costs = indirect_base * indirect_rate

        # Total
        total = total_direct + indirect_costs

        return {
            "by_category": {k: {"subtotal": float(v["subtotal"]), "items": v["items"]} for k, v in by_category.items()},
            "total_direct": float(total_direct),
            "indirect_base": float(indirect_base),
            "indirect_rate": float(indirect_rate),
            "indirect_costs": float(indirect_costs),
            "total": float(total),
        }

    @classmethod
    def generate_budget_narrative(cls, budget: Dict[str, Any]) -> str:
        """Generate budget narrative from calculated budget."""
        narrative_parts = []

        narrative_parts.append("## Budget Narrative\n")
        narrative_parts.append(f"**Total Project Cost:** ${budget['total']:,.2f}\n")
        narrative_parts.append(f"**Total Direct Costs:** ${budget['total_direct']:,.2f}\n")
        narrative_parts.append(f"**Indirect Costs ({budget['indirect_rate']*100:.1f}%):** ${budget['indirect_costs']:,.2f}\n\n")

        for category_id, category_data in budget["by_category"].items():
            category_info = cls.CATEGORIES.get(category_id, {"name": category_id.title()})
            narrative_parts.append(f"### {category_info['name']}\n")
            narrative_parts.append(f"**Subtotal:** ${category_data['subtotal']:,.2f}\n\n")

            for item in category_data["items"]:
                narrative_parts.append(f"- **{item.get('description', 'Item')}:** ${item.get('amount', 0):,.2f}")
                if item.get("justification"):
                    narrative_parts.append(f"\n  *Justification:* {item['justification']}")
                narrative_parts.append("\n")

            narrative_parts.append("\n")

        return "".join(narrative_parts)

    @classmethod
    def validate_budget(cls, budget: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Validate budget against constraints."""
        errors = []
        warnings = []

        # Check total limit
        if constraints.get("max_total"):
            if budget["total"] > constraints["max_total"]:
                errors.append(f"Total budget (${budget['total']:,.2f}) exceeds maximum allowed (${constraints['max_total']:,.2f})")

        # Check category limits
        category_limits = constraints.get("category_limits", {})
        for category, limit in category_limits.items():
            if category in budget["by_category"]:
                if budget["by_category"][category]["subtotal"] > limit:
                    errors.append(f"{category.title()} costs exceed limit of ${limit:,.2f}")

        # Check indirect rate
        if constraints.get("max_indirect_rate"):
            if budget["indirect_rate"] > constraints["max_indirect_rate"]:
                warnings.append(f"Indirect rate ({budget['indirect_rate']*100:.1f}%) exceeds typical maximum ({constraints['max_indirect_rate']*100:.1f}%)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


class BudgetCalculator:
    """Interactive budget calculator."""

    @staticmethod
    def calculate_personnel_cost(
        salary: float,
        percent_effort: float,
        months: int,
        fringe_rate: float = 0.30,
    ) -> Dict[str, float]:
        """Calculate personnel costs."""
        base_cost = (salary / 12) * months * (percent_effort / 100)
        fringe = base_cost * fringe_rate
        return {
            "base_salary": base_cost,
            "fringe_benefits": fringe,
            "total": base_cost + fringe,
        }

    @staticmethod
    def calculate_travel_cost(
        trips: int,
        days_per_trip: int,
        airfare: float,
        per_diem: float,
        lodging: float,
        ground_transport: float = 50,
    ) -> Dict[str, float]:
        """Calculate travel costs."""
        airfare_total = airfare * trips
        per_diem_total = per_diem * days_per_trip * trips
        lodging_total = lodging * (days_per_trip - 1) * trips  # Assumes travel days don't need lodging
        ground_total = ground_transport * trips

        return {
            "airfare": airfare_total,
            "per_diem": per_diem_total,
            "lodging": lodging_total,
            "ground_transport": ground_total,
            "total": airfare_total + per_diem_total + lodging_total + ground_total,
        }

    @staticmethod
    def calculate_equipment_depreciation(
        purchase_cost: float,
        useful_life_years: int,
        project_months: int,
    ) -> Dict[str, float]:
        """Calculate equipment depreciation for project period."""
        monthly_depreciation = purchase_cost / (useful_life_years * 12)
        project_depreciation = monthly_depreciation * project_months

        return {
            "purchase_cost": purchase_cost,
            "monthly_depreciation": monthly_depreciation,
            "project_cost": project_depreciation,
        }
