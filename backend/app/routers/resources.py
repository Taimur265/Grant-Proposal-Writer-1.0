"""Resource library API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.resource_library import (
    Resource, ResourceUsage, Checklist, ChecklistInstance, FundingHistory,
    ResourceType, ResourceCategory
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/resources", tags=["Resource Library"])


# Schemas
class ResourceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: ResourceType
    category: ResourceCategory
    content: str
    tags: Optional[List[str]] = None
    funder_types: Optional[List[str]] = None
    is_public: bool = False


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class ChecklistCreate(BaseModel):
    title: str
    description: Optional[str] = None
    checklist_type: str
    items: List[dict]
    is_template: bool = False
    is_public: bool = False


class FundingHistoryCreate(BaseModel):
    funder_name: str
    grant_title: str
    grant_number: Optional[str] = None
    amount: float
    start_date: datetime
    end_date: datetime
    status: str
    project_description: Optional[str] = None
    key_outcomes: Optional[str] = None
    contact_person: Optional[str] = None


# Resource endpoints
@router.post("/")
async def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new resource."""
    resource = Resource(
        user_id=current_user.id,
        word_count=len(data.content.split()),
        **data.dict()
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return {"id": str(resource.id), "title": resource.title}


@router.get("/")
async def list_resources(
    resource_type: Optional[ResourceType] = None,
    category: Optional[ResourceCategory] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    include_public: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List resources with filtering."""
    # Own resources
    stmt = select(Resource).where(
        Resource.user_id == current_user.id,
        Resource.is_current == True
    )

    if resource_type:
        stmt = stmt.where(Resource.resource_type == resource_type)
    if category:
        stmt = stmt.where(Resource.category == category)
    if search:
        stmt = stmt.where(
            Resource.title.ilike(f"%{search}%") |
            Resource.content.ilike(f"%{search}%")
        )

    result = await db.execute(stmt.order_by(Resource.updated_at.desc()))
    resources = list(result.scalars())

    # Add public resources if requested
    if include_public:
        public_stmt = select(Resource).where(
            Resource.is_public == True,
            Resource.user_id != current_user.id,
            Resource.is_current == True
        )
        if resource_type:
            public_stmt = public_stmt.where(Resource.resource_type == resource_type)
        if category:
            public_stmt = public_stmt.where(Resource.category == category)

        public_result = await db.execute(public_stmt)
        resources.extend(public_result.scalars())

    return {
        "resources": [
            {
                "id": str(r.id),
                "title": r.title,
                "description": r.description,
                "resource_type": r.resource_type.value,
                "category": r.category.value,
                "word_count": r.word_count,
                "tags": r.tags,
                "use_count": r.use_count,
                "is_public": r.is_public,
                "is_own": r.user_id == current_user.id,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in resources
        ]
    }


@router.get("/{resource_id}")
async def get_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get resource content."""
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Check access
    if resource.user_id != current_user.id and not resource.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": str(resource.id),
        "title": resource.title,
        "description": resource.description,
        "resource_type": resource.resource_type.value,
        "category": resource.category.value,
        "content": resource.content,
        "word_count": resource.word_count,
        "tags": resource.tags,
        "funder_types": resource.funder_types,
        "use_count": resource.use_count,
        "last_used_at": resource.last_used_at.isoformat() if resource.last_used_at else None,
        "is_public": resource.is_public,
    }


@router.patch("/{resource_id}")
async def update_resource(
    resource_id: UUID,
    data: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a resource."""
    resource = await db.get(Resource, resource_id)
    if not resource or resource.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resource not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(resource, key, value)

    if data.content:
        resource.word_count = len(data.content.split())

    await db.commit()
    return {"message": "Resource updated"}


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a resource."""
    resource = await db.get(Resource, resource_id)
    if not resource or resource.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)
    await db.commit()
    return {"message": "Resource deleted"}


@router.post("/{resource_id}/use")
async def use_resource(
    resource_id: UUID,
    proposal_id: Optional[UUID] = None,
    section_used_in: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track resource usage."""
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Log usage
    usage = ResourceUsage(
        resource_id=resource_id,
        proposal_id=proposal_id,
        used_by_id=current_user.id,
        section_used_in=section_used_in,
    )
    db.add(usage)

    # Update resource stats
    resource.use_count += 1
    resource.last_used_at = datetime.utcnow()

    await db.commit()
    return {"message": "Usage recorded", "content": resource.content}


# Checklist endpoints
@router.post("/checklists")
async def create_checklist(
    data: ChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a checklist template."""
    checklist = Checklist(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(checklist)
    await db.commit()
    return {"id": str(checklist.id)}


@router.get("/checklists")
async def list_checklists(
    checklist_type: Optional[str] = None,
    include_public: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List checklists."""
    stmt = select(Checklist).where(Checklist.user_id == current_user.id)
    if checklist_type:
        stmt = stmt.where(Checklist.checklist_type == checklist_type)

    result = await db.execute(stmt)
    checklists = list(result.scalars())

    if include_public:
        public_stmt = select(Checklist).where(
            Checklist.is_public == True,
            Checklist.user_id != current_user.id
        )
        public_result = await db.execute(public_stmt)
        checklists.extend(public_result.scalars())

    return {
        "checklists": [
            {
                "id": str(c.id),
                "title": c.title,
                "description": c.description,
                "checklist_type": c.checklist_type,
                "item_count": len(c.items),
                "is_template": c.is_template,
                "is_public": c.is_public,
            }
            for c in checklists
        ]
    }


@router.post("/checklists/{checklist_id}/instance")
async def create_checklist_instance(
    checklist_id: UUID,
    project_id: Optional[UUID] = None,
    proposal_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an instance of a checklist for a project/proposal."""
    checklist = await db.get(Checklist, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    instance = ChecklistInstance(
        checklist_id=checklist_id,
        project_id=project_id,
        proposal_id=proposal_id,
        title=checklist.title,
        items=[{**item, "completed": False} for item in checklist.items],
    )
    db.add(instance)
    await db.commit()
    return {"id": str(instance.id)}


@router.patch("/checklist-instances/{instance_id}/items/{item_index}")
async def update_checklist_item(
    instance_id: UUID,
    item_index: int,
    completed: bool,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a checklist item status."""
    instance = await db.get(ChecklistInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Checklist instance not found")

    if item_index >= len(instance.items):
        raise HTTPException(status_code=400, detail="Invalid item index")

    items = instance.items.copy()
    items[item_index]["completed"] = completed
    items[item_index]["completed_at"] = datetime.utcnow().isoformat() if completed else None
    items[item_index]["completed_by"] = str(current_user.id) if completed else None
    if notes:
        items[item_index]["notes"] = notes

    instance.items = items

    # Update completion percentage
    completed_count = sum(1 for item in items if item.get("completed"))
    instance.completion_percentage = (completed_count / len(items)) * 100

    if instance.completion_percentage == 100:
        instance.completed_at = datetime.utcnow()

    await db.commit()
    return {"completion_percentage": instance.completion_percentage}


# Funding History endpoints
@router.post("/funding-history")
async def add_funding_history(
    data: FundingHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add funding history record."""
    history = FundingHistory(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(history)
    await db.commit()
    return {"id": str(history.id)}


@router.get("/funding-history")
async def list_funding_history(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List funding history."""
    stmt = select(FundingHistory).where(FundingHistory.user_id == current_user.id)
    if status:
        stmt = stmt.where(FundingHistory.status == status)

    result = await db.execute(stmt.order_by(FundingHistory.end_date.desc()))

    return {
        "funding_history": [
            {
                "id": str(f.id),
                "funder_name": f.funder_name,
                "grant_title": f.grant_title,
                "amount": f.amount,
                "start_date": f.start_date.isoformat(),
                "end_date": f.end_date.isoformat(),
                "status": f.status,
                "can_use_as_reference": f.can_use_as_reference,
            }
            for f in result.scalars()
        ]
    }


@router.get("/categories")
async def get_resource_categories():
    """Get available resource types and categories."""
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in ResourceType
        ],
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in ResourceCategory
        ],
        "checklist_types": [
            {"value": "pre_submission", "label": "Pre-Submission"},
            {"value": "review", "label": "Review"},
            {"value": "compliance", "label": "Compliance"},
            {"value": "budget", "label": "Budget"},
            {"value": "narrative", "label": "Narrative"},
            {"value": "attachments", "label": "Attachments"},
        ],
    }
