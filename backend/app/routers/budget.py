"""Budget API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.budget import BudgetService, BudgetCalculator

router = APIRouter(prefix="/budget", tags=["Budget"])


class LineItem(BaseModel):
    """Budget line item."""
    category: str
    subcategory: Optional[str] = None
    description: str
    amount: float
    justification: Optional[str] = None


class BudgetSettings(BaseModel):
    """Budget calculation settings."""
    currency: str = "USD"
    indirect_rate: float = 0.0
    indirect_base: str = "mtdc"
    exclude_from_indirect: List[str] = []


class BudgetCalculationRequest(BaseModel):
    """Request for budget calculation."""
    line_items: List[LineItem]
    settings: BudgetSettings


class PersonnelCostRequest(BaseModel):
    """Request for personnel cost calculation."""
    salary: float
    percent_effort: float
    months: int
    fringe_rate: float = 0.30


class TravelCostRequest(BaseModel):
    """Request for travel cost calculation."""
    trips: int
    days_per_trip: int
    airfare: float
    per_diem: float
    lodging: float
    ground_transport: float = 50


class EquipmentDepreciationRequest(BaseModel):
    """Request for equipment depreciation calculation."""
    purchase_cost: float
    useful_life_years: int
    project_months: int


class BudgetValidationRequest(BaseModel):
    """Request for budget validation."""
    budget: Dict[str, Any]
    constraints: Dict[str, Any]


@router.get("/template/{grant_type}")
async def get_budget_template(grant_type: str = "default"):
    """Get budget template based on grant type."""
    template = BudgetService.get_budget_template(grant_type)
    return template


@router.get("/categories")
async def get_budget_categories():
    """Get all budget categories with subcategories."""
    return {"categories": BudgetService.CATEGORIES}


@router.post("/calculate")
async def calculate_budget(request: BudgetCalculationRequest):
    """Calculate complete budget from line items."""
    line_items = [item.dict() for item in request.line_items]
    settings = request.settings.dict()

    result = BudgetService.calculate_budget(line_items, settings)
    return result


@router.post("/narrative")
async def generate_budget_narrative(request: BudgetCalculationRequest):
    """Generate budget narrative from line items."""
    line_items = [item.dict() for item in request.line_items]
    settings = request.settings.dict()

    budget = BudgetService.calculate_budget(line_items, settings)
    narrative = BudgetService.generate_budget_narrative(budget)

    return {
        "budget": budget,
        "narrative": narrative,
    }


@router.post("/validate")
async def validate_budget(request: BudgetValidationRequest):
    """Validate budget against constraints."""
    result = BudgetService.validate_budget(request.budget, request.constraints)
    return result


@router.post("/calculate/personnel")
async def calculate_personnel_cost(request: PersonnelCostRequest):
    """Calculate personnel costs including fringe benefits."""
    result = BudgetCalculator.calculate_personnel_cost(
        salary=request.salary,
        percent_effort=request.percent_effort,
        months=request.months,
        fringe_rate=request.fringe_rate,
    )
    return result


@router.post("/calculate/travel")
async def calculate_travel_cost(request: TravelCostRequest):
    """Calculate travel costs."""
    result = BudgetCalculator.calculate_travel_cost(
        trips=request.trips,
        days_per_trip=request.days_per_trip,
        airfare=request.airfare,
        per_diem=request.per_diem,
        lodging=request.lodging,
        ground_transport=request.ground_transport,
    )
    return result


@router.post("/calculate/equipment-depreciation")
async def calculate_equipment_depreciation(request: EquipmentDepreciationRequest):
    """Calculate equipment depreciation for project period."""
    result = BudgetCalculator.calculate_equipment_depreciation(
        purchase_cost=request.purchase_cost,
        useful_life_years=request.useful_life_years,
        project_months=request.project_months,
    )
    return result
