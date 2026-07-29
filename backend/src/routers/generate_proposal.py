"""
generate_proposal.py — Endpoint to generate a proposal from a conversation.

Endpoint:
    POST /api/generate/proposal

Flow:
    1. Receive conversation_id from frontend
    2. Load all messages from PostgreSQL for that conversation
    3. Run the proposal generation pipeline (analyze → web search → write)
    4. Return the proposal content
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from src.auth.clerk_auth import get_current_user_clerk
from src.models.conversation import Conversation
from src.services.proposal_generator import generate_proposal

router = APIRouter(
    prefix="/api/generate",
    tags=["Proposal Generation"],
)


class GenerateProposalRequest(BaseModel):
    conversation_id: str


@router.post("/proposal")
def generate_proposal_endpoint(
    request: GenerateProposalRequest,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Generate a proposal by analyzing the full conversation.

    Steps:
        1. Load all messages from DB for the given conversation_id
        2. Analyze the chat to extract client requirements (Gemini)
        3. Search the web for market context (Tavily)
        4. Write the full proposal (Gemini)
        5. Return the proposal content
    """
    user_id = current_user.get("sub", "anonymous")

    # ── Load the conversation from PostgreSQL ─────────────────────────────────
    conv = db.query(Conversation).filter(
        Conversation.id == request.conversation_id,
        Conversation.user_id == user_id,
    ).first()

    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found. Make sure the conversation_id is correct."
        )

    if not conv.messages:
        raise HTTPException(
            status_code=400,
            detail="This conversation has no messages yet. Chat first, then generate a proposal."
        )

    # ── Convert DB messages to plain dicts ────────────────────────────────────
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in conv.messages
    ]

    print(f"[ProposalEndpoint] Loaded {len(messages)} messages for conversation {request.conversation_id}")

    # ── Run the pipeline ─────────────────────────────────────────────────────
    try:
        result = generate_proposal(messages)
    except Exception as exc:
        print(f"[ProposalEndpoint] Pipeline error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Proposal generation failed: {str(exc)}"
        )

    # ── Return the result ─────────────────────────────────────────────────────
    return {
        "proposal_content": result["proposal_content"],
        "requirements":     result["requirements"],
        "web_search_used":  result["web_search_used"],
        "message_count":    len(messages),
        "conversation_title": conv.title,
    }
