"""
conversations.py — Endpoints to manage conversation sessions.

Endpoints:
    POST   /api/conversations/          → Create a new conversation (get an ID)
    GET    /api/conversations/          → List all user's conversations (sidebar)
    GET    /api/conversations/{id}      → Load a specific conversation + messages
    DELETE /api/conversations/{id}      → Delete a conversation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from src.auth.clerk_auth import get_current_user_clerk
from src.models.conversation import Conversation, Message

router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — convert DB objects to plain dicts
# ─────────────────────────────────────────────────────────────────────────────

def _msg_to_dict(m: Message) -> dict:
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "role": m.role,
        "content": m.content,
        "timestamp": m.timestamp.isoformat(),
    }


def _conv_to_dict(c: Conversation, include_messages: bool = False) -> dict:
    data = {
        "id": c.id,
        "title": c.title,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }
    if include_messages:
        data["messages"] = [_msg_to_dict(m) for m in c.messages]
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Create a new conversation session.
    Called by frontend when user opens a new chat.
    Returns the conversation_id needed for saving messages.
    """
    user_id = current_user.get("sub", "anonymous")

    conv = Conversation(
        user_id=user_id,
        title=request.title or "New Conversation",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return _conv_to_dict(conv)


@router.get("/")
def list_conversations(
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Return all conversations for the current user, newest first.
    Used to populate the sidebar list.
    """
    user_id = current_user.get("sub", "anonymous")

    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_conv_to_dict(c) for c in convs]


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Load a specific conversation with all its messages.
    Called when user clicks on a past conversation in the sidebar.
    """
    user_id = current_user.get("sub", "anonymous")

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return _conv_to_dict(conv, include_messages=True)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Delete a conversation and all its messages.
    """
    user_id = current_user.get("sub", "anonymous")

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    db.delete(conv)
    db.commit()
