"""Funder database and opportunity tracking service."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.funder import (
    Funder, FunderType, GrantOpportunity, OpportunityStatus,
    GrantApplication, ApplicationStatus
)


class FunderService:
    """Service for managing funders and grant opportunities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_funders(
        self,
        query: Optional[str] = None,
        funder_type: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        min_award: Optional[float] = None,
        max_award: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search funders with filters."""
        stmt = select(Funder).where(Funder.is_active == True)

        if query:
            search_term = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Funder.name).like(search_term),
                    func.lower(Funder.description).like(search_term),
                )
            )

        if funder_type:
            stmt = stmt.where(Funder.funder_type == FunderType(funder_type))

        if min_award:
            stmt = stmt.where(Funder.typical_award_max >= min_award)

        if max_award:
            stmt = stmt.where(Funder.typical_award_min <= max_award)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt)

        # Get results
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)

        funders = []
        for funder in result.scalars():
            funders.append({
                "id": str(funder.id),
                "name": funder.name,
                "short_name": funder.short_name,
                "type": funder.funder_type.value,
                "description": funder.description[:200] if funder.description else None,
                "website": funder.website,
                "focus_areas": funder.focus_areas,
                "typical_award_min": funder.typical_award_min,
                "typical_award_max": funder.typical_award_max,
                "max_indirect_rate": funder.max_indirect_rate,
            })

        return {
            "funders": funders,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def search_opportunities(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        funder_id: Optional[UUID] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        closing_within_days: Optional[int] = None,
        focus_areas: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search grant opportunities with filters."""
        stmt = select(GrantOpportunity)

        if query:
            search_term = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(GrantOpportunity.title).like(search_term),
                    func.lower(GrantOpportunity.description).like(search_term),
                )
            )

        if status:
            stmt = stmt.where(GrantOpportunity.status == OpportunityStatus(status))
        else:
            # Default to open opportunities
            stmt = stmt.where(GrantOpportunity.status.in_([
                OpportunityStatus.OPEN,
                OpportunityStatus.CLOSING_SOON,
                OpportunityStatus.ROLLING,
            ]))

        if funder_id:
            stmt = stmt.where(GrantOpportunity.funder_id == funder_id)

        if min_amount:
            stmt = stmt.where(GrantOpportunity.award_ceiling >= min_amount)

        if max_amount:
            stmt = stmt.where(GrantOpportunity.award_floor <= max_amount)

        if closing_within_days:
            cutoff = datetime.utcnow() + timedelta(days=closing_within_days)
            stmt = stmt.where(
                and_(
                    GrantOpportunity.close_date.isnot(None),
                    GrantOpportunity.close_date <= cutoff,
                    GrantOpportunity.close_date >= datetime.utcnow(),
                )
            )

        # Order by close date
        stmt = stmt.order_by(GrantOpportunity.close_date.asc().nullslast())

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt)

        # Get results
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)

        opportunities = []
        for opp in result.scalars():
            days_until_close = None
            if opp.close_date:
                delta = opp.close_date - datetime.utcnow()
                days_until_close = max(0, delta.days)

            opportunities.append({
                "id": str(opp.id),
                "funder_id": str(opp.funder_id),
                "title": opp.title,
                "description": opp.description[:300] if opp.description else None,
                "status": opp.status.value,
                "award_floor": opp.award_floor,
                "award_ceiling": opp.award_ceiling,
                "close_date": opp.close_date.isoformat() if opp.close_date else None,
                "days_until_close": days_until_close,
                "focus_areas": opp.focus_areas,
                "is_bookmarked": opp.is_bookmarked,
                "match_score": opp.match_score,
            })

        return {
            "opportunities": opportunities,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_opportunity_details(self, opportunity_id: UUID) -> Optional[Dict[str, Any]]:
        """Get full details of a grant opportunity."""
        opp = await self.db.get(GrantOpportunity, opportunity_id)
        if not opp:
            return None

        # Get funder info
        funder = await self.db.get(Funder, opp.funder_id)

        days_until_close = None
        if opp.close_date:
            delta = opp.close_date - datetime.utcnow()
            days_until_close = max(0, delta.days)

        return {
            "id": str(opp.id),
            "title": opp.title,
            "description": opp.description,
            "program_url": opp.program_url,
            "opportunity_number": opp.opportunity_number,
            "status": opp.status.value,
            "funder": {
                "id": str(funder.id),
                "name": funder.name,
                "type": funder.funder_type.value,
                "website": funder.website,
            } if funder else None,
            "funding": {
                "award_floor": opp.award_floor,
                "award_ceiling": opp.award_ceiling,
                "expected_awards": opp.expected_awards,
                "total_funding": opp.total_funding,
                "cost_sharing_required": opp.cost_sharing_required,
                "cost_sharing_percentage": opp.cost_sharing_percentage,
            },
            "eligibility": {
                "eligible_applicants": opp.eligible_applicants,
                "notes": opp.eligibility_notes,
            },
            "dates": {
                "posted_date": opp.posted_date.isoformat() if opp.posted_date else None,
                "open_date": opp.open_date.isoformat() if opp.open_date else None,
                "close_date": opp.close_date.isoformat() if opp.close_date else None,
                "days_until_close": days_until_close,
                "estimated_award_date": opp.estimated_award_date.isoformat() if opp.estimated_award_date else None,
                "project_duration_months": opp.project_duration_months,
            },
            "requirements": {
                "required_documents": opp.required_documents,
                "page_limits": opp.page_limits,
                "submission_method": opp.submission_method,
            },
            "focus_areas": opp.focus_areas,
            "keywords": opp.keywords,
            "is_bookmarked": opp.is_bookmarked,
            "match_score": opp.match_score,
        }

    async def get_application_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get application statistics for a user."""
        # Total applications
        total = await self.db.scalar(
            select(func.count(GrantApplication.id)).where(
                GrantApplication.user_id == user_id
            )
        )

        # By status
        status_counts = {}
        for status in ApplicationStatus:
            count = await self.db.scalar(
                select(func.count(GrantApplication.id)).where(
                    and_(
                        GrantApplication.user_id == user_id,
                        GrantApplication.status == status,
                    )
                )
            )
            status_counts[status.value] = count

        # Success rate
        awarded = status_counts.get("awarded", 0)
        decided = awarded + status_counts.get("declined", 0)
        success_rate = (awarded / decided * 100) if decided > 0 else None

        # Total amounts
        total_requested = await self.db.scalar(
            select(func.sum(GrantApplication.requested_amount)).where(
                GrantApplication.user_id == user_id
            )
        ) or 0

        total_awarded = await self.db.scalar(
            select(func.sum(GrantApplication.awarded_amount)).where(
                and_(
                    GrantApplication.user_id == user_id,
                    GrantApplication.status == ApplicationStatus.AWARDED,
                )
            )
        ) or 0

        return {
            "total_applications": total,
            "by_status": status_counts,
            "success_rate": round(success_rate, 1) if success_rate else None,
            "total_requested": total_requested,
            "total_awarded": total_awarded,
        }

    async def get_upcoming_deadlines(self, user_id: UUID, days: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming grant deadlines."""
        cutoff = datetime.utcnow() + timedelta(days=days)

        # Get bookmarked opportunities with upcoming deadlines
        result = await self.db.execute(
            select(GrantOpportunity)
            .where(
                and_(
                    GrantOpportunity.is_bookmarked == True,
                    GrantOpportunity.close_date.isnot(None),
                    GrantOpportunity.close_date >= datetime.utcnow(),
                    GrantOpportunity.close_date <= cutoff,
                )
            )
            .order_by(GrantOpportunity.close_date.asc())
        )

        deadlines = []
        for opp in result.scalars():
            days_remaining = (opp.close_date - datetime.utcnow()).days
            deadlines.append({
                "id": str(opp.id),
                "title": opp.title,
                "funder_id": str(opp.funder_id),
                "close_date": opp.close_date.isoformat(),
                "days_remaining": days_remaining,
                "award_ceiling": opp.award_ceiling,
            })

        return deadlines


class OpportunityMatcher:
    """Service for matching opportunities to organization profile."""

    @staticmethod
    def calculate_match_score(
        opportunity: Dict[str, Any],
        organization_profile: Dict[str, Any],
    ) -> float:
        """Calculate compatibility score between opportunity and organization."""
        score = 0
        max_score = 100

        # Focus area match (40 points)
        opp_focus = set(opportunity.get("focus_areas", []))
        org_focus = set(organization_profile.get("focus_areas", []))
        if opp_focus and org_focus:
            overlap = len(opp_focus & org_focus)
            focus_score = min(40, (overlap / max(len(opp_focus), 1)) * 40)
            score += focus_score

        # Organization type eligibility (20 points)
        eligible_types = opportunity.get("eligible_applicants", [])
        org_type = organization_profile.get("organization_type", "")
        if not eligible_types or org_type.lower() in [e.lower() for e in eligible_types]:
            score += 20

        # Geographic match (15 points)
        opp_geo = set(opportunity.get("geographic_focus", []))
        org_location = organization_profile.get("location", "")
        if not opp_geo or org_location in opp_geo or "national" in [g.lower() for g in opp_geo]:
            score += 15

        # Award amount fit (15 points)
        org_budget = organization_profile.get("annual_budget", 0)
        award_ceiling = opportunity.get("award_ceiling", 0)
        if award_ceiling:
            # Check if award is reasonable relative to org size
            if award_ceiling <= org_budget * 0.5:
                score += 15
            elif award_ceiling <= org_budget:
                score += 10
            else:
                score += 5

        # Indirect rate compatibility (10 points)
        opp_max_indirect = opportunity.get("max_indirect_rate")
        org_indirect = organization_profile.get("indirect_rate", 0)
        if opp_max_indirect is None or org_indirect <= opp_max_indirect:
            score += 10

        return min(max_score, score)
