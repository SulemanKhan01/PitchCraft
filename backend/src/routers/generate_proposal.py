"""
generate_proposal.py — Endpoint to generate and download AB Ark proposal documents.

Endpoints:
    POST /api/generate/proposal      -> Returns proposal JSON markdown & extracted requirements
    POST /api/generate/proposal/docx -> Generates & downloads official AB {Ark} .docx file
"""

import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from src.auth.clerk_auth import get_current_user_clerk
from src.models.conversation import Conversation
from src.services.proposal_generator import generate_proposal
from src.services.proposal_generator.docx_generator import build_proposal_docx_from_markdown
from src.services.proposal_generator.utils import generate_proposal_id, get_formatted_current_date, get_default_version

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
    Generate a proposal by analyzing the full conversation via LangGraph.
    """
    user_id = current_user.get("sub", "anonymous")

    # Load conversation from PostgreSQL
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

    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in conv.messages
    ]

    print(f"[ProposalEndpoint] Loaded {len(messages)} messages for conversation {request.conversation_id}")

    try:
        result = generate_proposal(messages)
    except Exception as exc:
        print(f"[ProposalEndpoint] Pipeline error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Proposal generation failed: {str(exc)}"
        )

    return {
        "proposal_content": result["proposal_content"],
        "requirements":     result["requirements"],
        "web_search_used":  result["web_search_used"],
        "message_count":    len(messages),
        "conversation_title": conv.title,
    }


@router.post("/proposal/docx")
def download_proposal_docx(
    request: GenerateProposalRequest,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Generate and download official AB {Ark} .docx proposal document.
    Renders Page 1 Cover + Pages 2+ Body with dynamic metadata.
    """
    user_id = current_user.get("sub", "anonymous")

    conv = db.query(Conversation).filter(
        Conversation.id == request.conversation_id,
        Conversation.user_id == user_id,
    ).first()

    if not conv or not conv.messages:
        raise HTTPException(status_code=400, detail="Conversation has no messages to build proposal.")

    messages = [{"role": msg.role, "content": msg.content} for msg in conv.messages]

    # Run LangGraph pipeline to generate multi-section proposal markdown & requirements
    result = generate_proposal(messages)

    proposal_md = result.get("proposal_content") or ""
    reqs = result.get("requirements") or {}

    project_title = reqs.get("project_title") or conv.title or "Software Project"
    client_name = reqs.get("client_name") or "Valued Client"
    doc_id = generate_proposal_id()
    date_str = get_formatted_current_date()
    version = get_default_version()

    # Generate DOCX binary stream using master DOCX engine
    docx_bytes = build_proposal_docx_from_markdown(
        markdown_content=proposal_md,
        project_title=project_title,
        client_name=client_name,
        proposal_id=doc_id,
        date_str=date_str,
        version=version
    )

    clean_filename_title = project_title.replace(" ", "_").replace("/", "_")
    filename = f"AB_Ark_Proposal_{clean_filename_title}.docx"

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
