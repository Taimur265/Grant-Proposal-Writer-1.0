"""Reporting and metrics API routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.reporting import Report, Metric, MetricDataPoint, KPIDashboard, ReportType, ReportStatus, MetricType
from app.routers.auth import get_current_user

router = APIRouter(prefix="/reporting", tags=["Reporting"])


# Schemas
class ReportCreate(BaseModel):
    project_id: UUID
    title: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    due_date: Optional[datetime] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ReportStatus] = None
    executive_summary: Optional[str] = None
    activities_completed: Optional[str] = None
    objectives_progress: Optional[str] = None
    challenges: Optional[str] = None
    lessons_learned: Optional[str] = None
    next_steps: Optional[str] = None
    financial_narrative: Optional[str] = None
    budget_spent: Optional[float] = None
    budget_remaining: Optional[float] = None


class MetricCreate(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    metric_type: MetricType
    unit: str
    baseline_value: Optional[float] = None
    target_value: float
    data_source: Optional[str] = None
    collection_method: Optional[str] = None
    collection_frequency: Optional[str] = None


class MetricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    data_source: Optional[str] = None


class DataPointCreate(BaseModel):
    metric_id: UUID
    value: float
    recorded_date: datetime
    notes: Optional[str] = None


# Report endpoints
@router.post("/reports")
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new report."""
    report = Report(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {"id": str(report.id), "title": report.title}


@router.get("/reports")
async def list_reports(
    project_id: Optional[UUID] = None,
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List reports."""
    stmt = select(Report).where(Report.user_id == current_user.id)

    if project_id:
        stmt = stmt.where(Report.project_id == project_id)
    if report_type:
        stmt = stmt.where(Report.report_type == report_type)
    if status:
        stmt = stmt.where(Report.status == status)

    result = await db.execute(stmt.order_by(Report.created_at.desc()))

    return {
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "report_type": r.report_type.value,
                "status": r.status.value,
                "period_start": r.period_start.isoformat(),
                "period_end": r.period_end.isoformat(),
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in result.scalars()
        ]
    }


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get report details."""
    report = await db.get(Report, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": str(report.id),
        "title": report.title,
        "report_type": report.report_type.value,
        "status": report.status.value,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "due_date": report.due_date.isoformat() if report.due_date else None,
        "executive_summary": report.executive_summary,
        "activities_completed": report.activities_completed,
        "objectives_progress": report.objectives_progress,
        "challenges": report.challenges,
        "lessons_learned": report.lessons_learned,
        "next_steps": report.next_steps,
        "budget_spent": report.budget_spent,
        "budget_remaining": report.budget_remaining,
        "financial_narrative": report.financial_narrative,
        "expenditure_breakdown": report.expenditure_breakdown,
        "metrics_data": report.metrics_data,
        "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None,
    }


@router.patch("/reports/{report_id}")
async def update_report(
    report_id: UUID,
    data: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a report."""
    report = await db.get(Report, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(report, key, value)

    await db.commit()
    return {"message": "Report updated"}


@router.post("/reports/{report_id}/submit")
async def submit_report(
    report_id: UUID,
    submitted_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a report."""
    report = await db.get(Report, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = ReportStatus.SUBMITTED
    report.submitted_at = datetime.utcnow()
    if submitted_to:
        report.submitted_to = submitted_to

    await db.commit()
    return {"message": "Report submitted"}


# Metric endpoints
@router.post("/metrics")
async def create_metric(
    data: MetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new metric."""
    metric = Metric(
        user_id=current_user.id,
        **data.dict()
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return {"id": str(metric.id), "name": metric.name}


@router.get("/metrics")
async def list_metrics(
    project_id: Optional[UUID] = None,
    metric_type: Optional[MetricType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List metrics."""
    stmt = select(Metric).where(
        Metric.user_id == current_user.id,
        Metric.is_active == True
    )

    if project_id:
        stmt = stmt.where(Metric.project_id == project_id)
    if metric_type:
        stmt = stmt.where(Metric.metric_type == metric_type)

    result = await db.execute(stmt.order_by(Metric.name))

    return {
        "metrics": [
            {
                "id": str(m.id),
                "name": m.name,
                "metric_type": m.metric_type.value,
                "unit": m.unit,
                "baseline_value": m.baseline_value,
                "target_value": m.target_value,
                "current_value": m.current_value,
                "progress_percentage": m.progress_percentage,
                "on_track": m.on_track,
            }
            for m in result.scalars()
        ]
    }


@router.get("/metrics/{metric_id}")
async def get_metric(
    metric_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get metric details with historical data."""
    metric = await db.get(Metric, metric_id)
    if not metric or metric.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Get historical data points
    data_result = await db.execute(
        select(MetricDataPoint)
        .where(MetricDataPoint.metric_id == metric_id)
        .order_by(MetricDataPoint.recorded_date)
    )

    return {
        "id": str(metric.id),
        "name": metric.name,
        "description": metric.description,
        "metric_type": metric.metric_type.value,
        "unit": metric.unit,
        "baseline_value": metric.baseline_value,
        "target_value": metric.target_value,
        "current_value": metric.current_value,
        "progress_percentage": metric.progress_percentage,
        "on_track": metric.on_track,
        "data_source": metric.data_source,
        "collection_method": metric.collection_method,
        "collection_frequency": metric.collection_frequency,
        "data_points": [
            {
                "value": dp.value,
                "date": dp.recorded_date.isoformat(),
                "notes": dp.notes,
            }
            for dp in data_result.scalars()
        ],
    }


@router.patch("/metrics/{metric_id}")
async def update_metric(
    metric_id: UUID,
    data: MetricUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a metric."""
    metric = await db.get(Metric, metric_id)
    if not metric or metric.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Metric not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(metric, key, value)

    # Recalculate progress
    if metric.target_value and metric.target_value > 0:
        baseline = metric.baseline_value or 0
        progress = ((metric.current_value - baseline) / (metric.target_value - baseline)) * 100
        metric.progress_percentage = min(max(progress, 0), 100)

    await db.commit()
    return {"message": "Metric updated"}


@router.post("/metrics/data-points")
async def record_data_point(
    data: DataPointCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a data point for a metric."""
    metric = await db.get(Metric, data.metric_id)
    if not metric or metric.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Metric not found")

    data_point = MetricDataPoint(
        metric_id=data.metric_id,
        value=data.value,
        recorded_date=data.recorded_date,
        recorded_by=current_user.id,
        notes=data.notes,
    )
    db.add(data_point)

    # Update current value if this is the latest
    metric.current_value = data.value

    # Recalculate progress
    if metric.target_value and metric.target_value > 0:
        baseline = metric.baseline_value or 0
        progress = ((metric.current_value - baseline) / (metric.target_value - baseline)) * 100
        metric.progress_percentage = min(max(progress, 0), 100)

    await db.commit()
    return {"id": str(data_point.id)}


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reporting dashboard summary."""
    # Metrics summary
    metrics_stmt = select(Metric).where(
        Metric.user_id == current_user.id,
        Metric.is_active == True
    )
    if project_id:
        metrics_stmt = metrics_stmt.where(Metric.project_id == project_id)

    metrics_result = await db.execute(metrics_stmt)
    metrics = list(metrics_result.scalars())

    on_track = sum(1 for m in metrics if m.on_track)
    off_track = len(metrics) - on_track

    # Reports summary
    reports_stmt = select(Report).where(Report.user_id == current_user.id)
    if project_id:
        reports_stmt = reports_stmt.where(Report.project_id == project_id)

    reports_result = await db.execute(reports_stmt)
    reports = list(reports_result.scalars())

    # Upcoming reports
    now = datetime.utcnow()
    upcoming = [r for r in reports if r.due_date and r.due_date > now and r.status != ReportStatus.SUBMITTED]

    return {
        "metrics": {
            "total": len(metrics),
            "on_track": on_track,
            "off_track": off_track,
            "avg_progress": sum(m.progress_percentage for m in metrics) / len(metrics) if metrics else 0,
        },
        "reports": {
            "total": len(reports),
            "draft": sum(1 for r in reports if r.status == ReportStatus.DRAFT),
            "submitted": sum(1 for r in reports if r.status == ReportStatus.SUBMITTED),
            "upcoming_count": len(upcoming),
        },
        "upcoming_reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "due_date": r.due_date.isoformat(),
                "days_until": (r.due_date - now).days,
            }
            for r in sorted(upcoming, key=lambda x: x.due_date)[:5]
        ],
    }


@router.get("/report-types")
async def get_report_types():
    """Get available report types."""
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in ReportType
        ],
        "statuses": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in ReportStatus
        ],
        "metric_types": [
            {"value": m.value, "label": m.value.title()}
            for m in MetricType
        ],
    }
