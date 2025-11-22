"""Search service for full-text search across the application."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, text
from sqlalchemy.orm import joinedload

from app.models.project import Project
from app.models.document import Document
from app.models.proposal import Proposal, ProposalSection


class SearchService:
    """Service for searching across projects, documents, and proposals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_all(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
        include_projects: bool = True,
        include_documents: bool = True,
        include_proposals: bool = True,
    ) -> Dict[str, Any]:
        """Search across all entities."""
        results = {
            "query": query,
            "total_results": 0,
            "projects": [],
            "documents": [],
            "proposals": [],
        }

        search_term = f"%{query.lower()}%"

        # Get user's project IDs
        project_ids_result = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        user_project_ids = list(project_ids_result)

        if not user_project_ids:
            return results

        if include_projects:
            projects = await self._search_projects(user_id, search_term, limit)
            results["projects"] = projects
            results["total_results"] += len(projects)

        if include_documents:
            documents = await self._search_documents(user_project_ids, search_term, limit)
            results["documents"] = documents
            results["total_results"] += len(documents)

        if include_proposals:
            proposals = await self._search_proposals(user_project_ids, search_term, limit)
            results["proposals"] = proposals
            results["total_results"] += len(proposals)

        return results

    async def _search_projects(
        self, user_id: UUID, search_term: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search projects by name and description."""
        result = await self.db.execute(
            select(Project)
            .where(
                Project.owner_id == user_id,
                or_(
                    func.lower(Project.name).like(search_term),
                    func.lower(Project.description).like(search_term),
                    func.lower(Project.grant_type).like(search_term),
                ),
            )
            .limit(limit)
        )

        projects = []
        for project in result.scalars():
            projects.append({
                "id": str(project.id),
                "type": "project",
                "name": project.name,
                "description": project.description[:200] if project.description else None,
                "status": project.status.value,
                "created_at": project.created_at.isoformat(),
                "highlight": self._get_highlight(
                    [project.name, project.description or ""],
                    search_term.strip("%")
                ),
            })

        return projects

    async def _search_documents(
        self, project_ids: List[UUID], search_term: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search documents by filename and extracted content."""
        result = await self.db.execute(
            select(Document)
            .where(
                Document.project_id.in_(project_ids),
                or_(
                    func.lower(Document.original_filename).like(search_term),
                    func.lower(Document.extracted_text).like(search_term),
                ),
            )
            .limit(limit)
        )

        documents = []
        for doc in result.scalars():
            documents.append({
                "id": str(doc.id),
                "type": "document",
                "name": doc.original_filename,
                "project_id": str(doc.project_id),
                "category": doc.category.value,
                "document_type": doc.document_type.value,
                "created_at": doc.created_at.isoformat(),
                "highlight": self._get_highlight(
                    [doc.original_filename, doc.extracted_text or ""],
                    search_term.strip("%")
                ),
            })

        return documents

    async def _search_proposals(
        self, project_ids: List[UUID], search_term: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Search proposals by title and content."""
        result = await self.db.execute(
            select(Proposal)
            .where(
                Proposal.project_id.in_(project_ids),
                or_(
                    func.lower(Proposal.title).like(search_term),
                    func.lower(Proposal.content).like(search_term),
                ),
            )
            .limit(limit)
        )

        proposals = []
        for proposal in result.scalars():
            proposals.append({
                "id": str(proposal.id),
                "type": "proposal",
                "name": proposal.title,
                "project_id": str(proposal.project_id),
                "status": proposal.status.value,
                "word_count": proposal.word_count,
                "created_at": proposal.created_at.isoformat(),
                "highlight": self._get_highlight(
                    [proposal.title, proposal.content or ""],
                    search_term.strip("%")
                ),
            })

        return proposals

    def _get_highlight(self, texts: List[str], query: str) -> Optional[str]:
        """Get highlighted snippet containing the search query."""
        query_lower = query.lower()

        for text in texts:
            if not text:
                continue
            text_lower = text.lower()
            pos = text_lower.find(query_lower)

            if pos != -1:
                # Get surrounding context
                start = max(0, pos - 50)
                end = min(len(text), pos + len(query) + 50)

                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."

                return snippet

        return None

    async def get_recent_items(
        self, user_id: UUID, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recently accessed/modified items."""
        recent = []

        # Get user's project IDs
        project_ids_result = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        user_project_ids = list(project_ids_result)

        if not user_project_ids:
            return recent

        # Recent projects
        recent_projects = await self.db.execute(
            select(Project)
            .where(Project.owner_id == user_id)
            .order_by(Project.updated_at.desc())
            .limit(5)
        )

        for project in recent_projects.scalars():
            recent.append({
                "id": str(project.id),
                "type": "project",
                "name": project.name,
                "updated_at": project.updated_at.isoformat(),
            })

        # Recent documents
        recent_docs = await self.db.execute(
            select(Document)
            .where(Document.project_id.in_(user_project_ids))
            .order_by(Document.updated_at.desc())
            .limit(5)
        )

        for doc in recent_docs.scalars():
            recent.append({
                "id": str(doc.id),
                "type": "document",
                "name": doc.original_filename,
                "project_id": str(doc.project_id),
                "updated_at": doc.updated_at.isoformat(),
            })

        # Recent proposals
        recent_proposals = await self.db.execute(
            select(Proposal)
            .where(Proposal.project_id.in_(user_project_ids))
            .order_by(Proposal.updated_at.desc())
            .limit(5)
        )

        for proposal in recent_proposals.scalars():
            recent.append({
                "id": str(proposal.id),
                "type": "proposal",
                "name": proposal.title,
                "project_id": str(proposal.project_id),
                "updated_at": proposal.updated_at.isoformat(),
            })

        # Sort by updated_at and limit
        recent.sort(key=lambda x: x["updated_at"], reverse=True)
        return recent[:limit]

    async def get_suggestions(
        self, user_id: UUID, partial_query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get search suggestions based on partial query."""
        suggestions = []
        search_term = f"{partial_query.lower()}%"

        # Get user's project IDs
        project_ids_result = await self.db.scalars(
            select(Project.id).where(Project.owner_id == user_id)
        )
        user_project_ids = list(project_ids_result)

        # Project name suggestions
        project_suggestions = await self.db.execute(
            select(Project.name)
            .where(
                Project.owner_id == user_id,
                func.lower(Project.name).like(search_term),
            )
            .limit(limit)
        )

        for (name,) in project_suggestions:
            suggestions.append({"text": name, "type": "project"})

        if user_project_ids:
            # Document name suggestions
            doc_suggestions = await self.db.execute(
                select(Document.original_filename)
                .where(
                    Document.project_id.in_(user_project_ids),
                    func.lower(Document.original_filename).like(search_term),
                )
                .limit(limit)
            )

            for (filename,) in doc_suggestions:
                suggestions.append({"text": filename, "type": "document"})

            # Proposal title suggestions
            proposal_suggestions = await self.db.execute(
                select(Proposal.title)
                .where(
                    Proposal.project_id.in_(user_project_ids),
                    func.lower(Proposal.title).like(search_term),
                )
                .limit(limit)
            )

            for (title,) in proposal_suggestions:
                suggestions.append({"text": title, "type": "proposal"})

        return suggestions[:limit]
