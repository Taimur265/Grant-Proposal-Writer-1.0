"""AI Chat Assistant API routes."""

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.proposal import Proposal
from app.models.document import Document
from app.routers.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


# In-memory chat history (in production, use database)
chat_sessions: dict = {}


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    project_id: Optional[UUID] = None
    context_type: Optional[str] = None  # proposal, budget, compliance, general


class ChatResponse(BaseModel):
    response: str
    session_id: str
    suggestions: List[str] = []


# Predefined responses and knowledge base
GRANT_WRITING_KNOWLEDGE = {
    "executive_summary": {
        "tips": [
            "Keep it concise - typically 1 page or less",
            "Write it last, but place it first",
            "Include: problem, solution, organization qualifications, funding request",
            "Hook the reader in the first sentence",
        ],
        "common_issues": [
            "Too long or too detailed",
            "Missing key elements",
            "Doesn't match the full proposal",
        ],
    },
    "needs_statement": {
        "tips": [
            "Use data and statistics to support your claims",
            "Focus on the community need, not your organization's need for funding",
            "Connect the need to your proposed solution",
            "Cite credible sources",
        ],
        "common_issues": [
            "Lack of supporting data",
            "Focusing on organizational needs",
            "Not clearly defining the target population",
        ],
    },
    "methodology": {
        "tips": [
            "Be specific about activities and timelines",
            "Explain why your approach will work",
            "Include measurable objectives",
            "Address potential challenges",
        ],
        "common_issues": [
            "Vague or unrealistic timelines",
            "Missing evaluation plan",
            "Not aligned with stated objectives",
        ],
    },
    "budget": {
        "tips": [
            "Ensure all costs are reasonable and allowable",
            "Provide detailed justifications",
            "Check funder's indirect rate limits",
            "Include all required budget categories",
        ],
        "common_issues": [
            "Math errors",
            "Missing cost justifications",
            "Exceeding budget limits",
            "Unallowable costs",
        ],
    },
    "evaluation": {
        "tips": [
            "Define clear, measurable outcomes",
            "Include both process and outcome evaluation",
            "Specify data collection methods",
            "Plan for reporting",
        ],
        "common_issues": [
            "Vague or unmeasurable outcomes",
            "No baseline data",
            "Unrealistic targets",
        ],
    },
}

QUICK_RESPONSES = {
    "hello": "Hello! I'm your grant writing assistant. I can help you with:\n\n- Writing and improving proposal sections\n- Budget development and justification\n- Compliance checking\n- Best practices for grant writing\n- Answering questions about specific funders\n\nWhat would you like help with today?",

    "help": "I can assist you with:\n\n**Proposal Writing**\n- Executive summary tips\n- Needs statement development\n- Methodology and timeline\n- Evaluation plan\n\n**Budget**\n- Cost categories\n- Justifications\n- Indirect rates\n\n**Compliance**\n- Checking requirements\n- Formatting guidelines\n- Eligibility verification\n\nJust ask a question or tell me what section you're working on!",
}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with the AI assistant."""
    # Get or create session
    session_id = request.session_id or str(uuid4())

    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "user_id": str(current_user.id),
            "messages": [],
            "context": {},
        }

    session = chat_sessions[session_id]

    # Load project context if provided
    context = ""
    if request.project_id:
        project = await db.get(Project, request.project_id)
        if project and project.owner_id == current_user.id:
            context = f"Project: {project.name}\n"
            if project.funder_name:
                context += f"Funder: {project.funder_name}\n"
            session["context"]["project"] = {
                "id": str(project.id),
                "name": project.name,
            }

    # Add user message to history
    user_message = {
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["messages"].append(user_message)

    # Generate response
    response_text, suggestions = await generate_response(
        request.message,
        session["messages"],
        request.context_type,
        context,
    )

    # Add assistant response to history
    assistant_message = {
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["messages"].append(assistant_message)

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        suggestions=suggestions,
    )


async def generate_response(
    message: str,
    history: List[dict],
    context_type: Optional[str],
    project_context: str,
) -> tuple[str, List[str]]:
    """Generate AI response based on message and context."""
    message_lower = message.lower().strip()

    # Check for quick responses
    for key, response in QUICK_RESPONSES.items():
        if key in message_lower:
            return response, ["Tell me more about proposal writing", "Help with budget", "Check compliance"]

    # Check for knowledge base queries
    suggestions = []

    if any(word in message_lower for word in ["executive summary", "abstract", "overview"]):
        knowledge = GRANT_WRITING_KNOWLEDGE["executive_summary"]
        response = format_knowledge_response("Executive Summary", knowledge)
        suggestions = ["Show me an example", "Common mistakes to avoid", "How long should it be?"]
        return response, suggestions

    if any(word in message_lower for word in ["need", "problem statement", "needs statement"]):
        knowledge = GRANT_WRITING_KNOWLEDGE["needs_statement"]
        response = format_knowledge_response("Needs Statement", knowledge)
        suggestions = ["How to find data", "Target population tips", "Example needs statements"]
        return response, suggestions

    if any(word in message_lower for word in ["method", "approach", "activities", "implementation"]):
        knowledge = GRANT_WRITING_KNOWLEDGE["methodology"]
        response = format_knowledge_response("Methodology", knowledge)
        suggestions = ["Timeline templates", "Logic model help", "Objective writing tips"]
        return response, suggestions

    if any(word in message_lower for word in ["budget", "cost", "expense", "funding"]):
        knowledge = GRANT_WRITING_KNOWLEDGE["budget"]
        response = format_knowledge_response("Budget", knowledge)
        suggestions = ["Budget categories explained", "Indirect cost rates", "Justification examples"]
        return response, suggestions

    if any(word in message_lower for word in ["evaluat", "measure", "outcome", "impact"]):
        knowledge = GRANT_WRITING_KNOWLEDGE["evaluation"]
        response = format_knowledge_response("Evaluation", knowledge)
        suggestions = ["SMART objectives", "Data collection methods", "Outcome indicators"]
        return response, suggestions

    if any(word in message_lower for word in ["compliance", "requirement", "eligible", "deadline"]):
        response = """**Compliance Tips**

Before submitting, ensure you've checked:

1. **Eligibility** - Verify your organization type qualifies
2. **Page/Word Limits** - Stay within specified limits
3. **Required Sections** - Include all mandatory components
4. **Formatting** - Follow font, margin, spacing requirements
5. **Attachments** - Include all required documents
6. **Deadline** - Submit before the deadline (not at the last minute!)

Would you like me to help check your proposal against specific requirements?"""
        suggestions = ["Check my proposal", "Formatting guidelines", "Common compliance issues"]
        return response, suggestions

    # Default response
    response = """I'm here to help with your grant writing needs. I can assist with:

- **Proposal sections**: Executive summary, needs statement, methodology, evaluation
- **Budget**: Categories, justifications, calculations
- **Compliance**: Requirements checking, formatting
- **Best practices**: Tips for stronger proposals

What specific aspect would you like help with?"""

    suggestions = [
        "Help with executive summary",
        "Budget tips",
        "Compliance checklist",
        "Improve my proposal",
    ]

    return response, suggestions


def format_knowledge_response(section: str, knowledge: dict) -> str:
    """Format knowledge base content into a readable response."""
    response = f"**{section} Tips**\n\n"

    response += "Key recommendations:\n"
    for tip in knowledge["tips"]:
        response += f"- {tip}\n"

    response += "\n**Common Issues to Avoid:**\n"
    for issue in knowledge["common_issues"]:
        response += f"- {issue}\n"

    return response


@router.get("/sessions")
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
):
    """List user's chat sessions."""
    user_sessions = []
    for session_id, session in chat_sessions.items():
        if session["user_id"] == str(current_user.id):
            user_sessions.append({
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "context": session.get("context", {}),
                "last_message": session["messages"][-1]["timestamp"] if session["messages"] else None,
            })

    return {"sessions": user_sessions}


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific chat session."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = chat_sessions[session_id]
    if session["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "session_id": session_id,
        "messages": session["messages"],
        "context": session.get("context", {}),
    }


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = chat_sessions[session_id]
    if session["user_id"] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    del chat_sessions[session_id]
    return {"message": "Session deleted"}


@router.get("/prompts")
async def get_suggested_prompts(
    context_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get suggested prompts based on context."""
    general_prompts = [
        "How do I write a compelling executive summary?",
        "What should I include in my needs statement?",
        "Help me develop SMART objectives",
        "What's the best way to justify budget costs?",
        "How do I create an evaluation plan?",
        "What are common grant writing mistakes?",
    ]

    context_prompts = {
        "proposal": [
            "Review my proposal structure",
            "Strengthen my problem statement",
            "Improve my methodology section",
            "Check my logic model",
        ],
        "budget": [
            "Explain budget categories",
            "Help with cost justifications",
            "Calculate indirect costs",
            "Check for allowable expenses",
        ],
        "compliance": [
            "Review eligibility requirements",
            "Check formatting guidelines",
            "Verify required sections",
            "Review deadline requirements",
        ],
    }

    prompts = general_prompts
    if context_type and context_type in context_prompts:
        prompts = context_prompts[context_type] + general_prompts[:2]

    return {"prompts": prompts}
