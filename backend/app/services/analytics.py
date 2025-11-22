"""Analytics service for dashboard metrics and insights."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.project import Project, ProjectStatus
from app.models.document import Document, DocumentCategory
from app.models.proposal import Proposal, ProposalStatus


class AnalyticsService:
    """Service for generating analytics and insights."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_dashboard_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics for a user."""
        # Get project counts by status
        project_stats = await self._get_project_stats(user_id)

        # Get document counts
        document_stats = await self._get_document_stats(user_id)

        # Get proposal stats
        proposal_stats = await self._get_proposal_stats(user_id)

        # Get recent activity
        recent_activity = await self._get_recent_activity(user_id)

        # Get upcoming deadlines
        upcoming_deadlines = await self._get_upcoming_deadlines(user_id)

        return {
            "projects": project_stats,
            "documents": document_stats,
            "proposals": proposal_stats,
            "recent_activity": recent_activity,
            "upcoming_deadlines": upcoming_deadlines,
        }

    async def _get_project_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get project statistics."""
        # Total projects
        total = await self.db.scalar(
            select(func.count(Project.id)).where(Project.owner_id == user_id)
        )

        # Projects by status
        status_counts = {}
        for status in ProjectStatus:
            count = await self.db.scalar(
                select(func.count(Project.id)).where(
                    and_(Project.owner_id == user_id, Project.status == status)
                )
            )
            status_counts[status.value] = count

        # Projects created this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = await self.db.scalar(
            select(func.count(Project.id)).where(
                and_(Project.owner_id == user_id, Project.created_at >= month_start)
            )
        )

        return {
            "total": total,
            "by_status": status_counts,
            "this_month": this_month,
        }

    async def _get_document_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get document statistics."""
        # Get all user's project IDs
        project_ids = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        project_ids = list(project_ids)

        if not project_ids:
            return {
                "total": 0,
                "by_category": {},
                "by_status": {},
                "total_size_mb": 0,
            }

        # Total documents
        total = await self.db.scalar(
            select(func.count(Document.id)).where(Document.project_id.in_(project_ids))
        )

        # By category
        category_counts = {}
        for category in DocumentCategory:
            count = await self.db.scalar(
                select(func.count(Document.id)).where(
                    and_(
                        Document.project_id.in_(project_ids),
                        Document.category == category,
                    )
                )
            )
            category_counts[category.value] = count

        # By processing status
        status_counts = {}
        for status in ["pending", "processing", "completed", "failed"]:
            count = await self.db.scalar(
                select(func.count(Document.id)).where(
                    and_(
                        Document.project_id.in_(project_ids),
                        Document.processing_status == status,
                    )
                )
            )
            status_counts[status] = count

        # Total file size
        total_size = await self.db.scalar(
            select(func.sum(Document.file_size)).where(Document.project_id.in_(project_ids))
        ) or 0

        return {
            "total": total,
            "by_category": category_counts,
            "by_status": status_counts,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    async def _get_proposal_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get proposal statistics."""
        # Get all user's project IDs
        project_ids = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        project_ids = list(project_ids)

        if not project_ids:
            return {
                "total": 0,
                "by_status": {},
                "avg_compliance_score": None,
                "total_words": 0,
            }

        # Total proposals
        total = await self.db.scalar(
            select(func.count(Proposal.id)).where(Proposal.project_id.in_(project_ids))
        )

        # By status
        status_counts = {}
        for status in ProposalStatus:
            count = await self.db.scalar(
                select(func.count(Proposal.id)).where(
                    and_(
                        Proposal.project_id.in_(project_ids),
                        Proposal.status == status,
                    )
                )
            )
            status_counts[status.value] = count

        # Average compliance score
        avg_score = await self.db.scalar(
            select(func.avg(Proposal.compliance_score)).where(
                and_(
                    Proposal.project_id.in_(project_ids),
                    Proposal.compliance_score.isnot(None),
                )
            )
        )

        # Total word count
        total_words = await self.db.scalar(
            select(func.sum(Proposal.word_count)).where(Proposal.project_id.in_(project_ids))
        ) or 0

        return {
            "total": total,
            "by_status": status_counts,
            "avg_compliance_score": round(avg_score, 1) if avg_score else None,
            "total_words": total_words,
        }

    async def _get_recent_activity(self, user_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity across projects, documents, and proposals."""
        activities = []

        # Get all user's project IDs
        project_ids = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        project_ids = list(project_ids)

        if not project_ids:
            return activities

        # Recent documents
        recent_docs = await self.db.execute(
            select(Document)
            .where(Document.project_id.in_(project_ids))
            .order_by(Document.created_at.desc())
            .limit(5)
        )
        for doc in recent_docs.scalars():
            activities.append({
                "type": "document_uploaded",
                "title": f"Uploaded {doc.original_filename}",
                "project_id": str(doc.project_id),
                "timestamp": doc.created_at.isoformat(),
            })

        # Recent proposals
        recent_proposals = await self.db.execute(
            select(Proposal)
            .where(Proposal.project_id.in_(project_ids))
            .order_by(Proposal.created_at.desc())
            .limit(5)
        )
        for proposal in recent_proposals.scalars():
            activities.append({
                "type": "proposal_created",
                "title": f"Generated {proposal.title}",
                "project_id": str(proposal.project_id),
                "timestamp": proposal.created_at.isoformat(),
            })

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]

    async def _get_upcoming_deadlines(self, user_id: UUID, days: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming project deadlines."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)

        result = await self.db.execute(
            select(Project)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deadline.isnot(None),
                    Project.deadline >= datetime.utcnow(),
                    Project.deadline <= cutoff_date,
                )
            )
            .order_by(Project.deadline.asc())
        )

        deadlines = []
        for project in result.scalars():
            days_remaining = (project.deadline - datetime.utcnow()).days
            deadlines.append({
                "project_id": str(project.id),
                "project_name": project.name,
                "deadline": project.deadline.isoformat(),
                "days_remaining": days_remaining,
                "status": project.status.value,
            })

        return deadlines

    async def get_project_insights(self, project_id: UUID) -> Dict[str, Any]:
        """Get detailed insights for a specific project."""
        project = await self.db.get(Project, project_id)
        if not project:
            return {}

        # Document analysis
        docs = await self.db.execute(
            select(Document).where(Document.project_id == project_id)
        )
        documents = docs.scalars().all()

        guidelines_count = sum(1 for d in documents if d.category == DocumentCategory.GUIDELINES)
        beneficiary_count = sum(1 for d in documents if d.category == DocumentCategory.BENEFICIARY)
        processed_count = sum(1 for d in documents if d.processing_status == "completed")

        # Proposal analysis
        proposals = await self.db.execute(
            select(Proposal).where(Proposal.project_id == project_id)
        )
        proposals_list = proposals.scalars().all()

        best_score = max((p.compliance_score for p in proposals_list if p.compliance_score), default=None)
        latest_proposal = max(proposals_list, key=lambda p: p.created_at, default=None)

        # Readiness assessment
        readiness = self._calculate_readiness(
            guidelines_count, beneficiary_count, processed_count, len(documents)
        )

        return {
            "documents": {
                "total": len(documents),
                "guidelines": guidelines_count,
                "beneficiary": beneficiary_count,
                "processed": processed_count,
                "pending": len(documents) - processed_count,
            },
            "proposals": {
                "total": len(proposals_list),
                "best_compliance_score": best_score,
                "latest": {
                    "id": str(latest_proposal.id),
                    "title": latest_proposal.title,
                    "status": latest_proposal.status.value,
                } if latest_proposal else None,
            },
            "readiness": readiness,
            "recommendations": self._get_recommendations(
                guidelines_count, beneficiary_count, processed_count, len(proposals_list)
            ),
        }

    def _calculate_readiness(
        self,
        guidelines_count: int,
        beneficiary_count: int,
        processed_count: int,
        total_docs: int,
    ) -> Dict[str, Any]:
        """Calculate project readiness for proposal generation."""
        score = 0
        max_score = 100

        # Has guidelines (40 points)
        if guidelines_count > 0:
            score += min(40, guidelines_count * 20)

        # Has beneficiary info (30 points)
        if beneficiary_count > 0:
            score += min(30, beneficiary_count * 15)

        # Documents processed (30 points)
        if total_docs > 0:
            process_rate = processed_count / total_docs
            score += int(30 * process_rate)

        status = "ready" if score >= 70 else "partial" if score >= 40 else "not_ready"

        return {
            "score": score,
            "max_score": max_score,
            "status": status,
            "can_generate": score >= 40,
        }

    def _get_recommendations(
        self,
        guidelines_count: int,
        beneficiary_count: int,
        processed_count: int,
        proposals_count: int,
    ) -> List[str]:
        """Get recommendations for improving the project."""
        recommendations = []

        if guidelines_count == 0:
            recommendations.append("Upload grant guidelines or RFP documents to get started")
        elif guidelines_count < 2:
            recommendations.append("Consider uploading additional guidelines documents like eligibility criteria or evaluation rubric")

        if beneficiary_count == 0:
            recommendations.append("Add beneficiary information such as organization profile and project description")
        elif beneficiary_count < 3:
            recommendations.append("Strengthen your proposal by adding more beneficiary documents like financial statements or team CVs")

        if guidelines_count > 0 and beneficiary_count > 0 and proposals_count == 0:
            recommendations.append("You're ready to generate your first proposal!")

        if proposals_count > 0:
            recommendations.append("Review your generated proposal and use compliance checking to identify improvements")

        return recommendations
