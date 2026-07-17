import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai


from fastapi import Depends
from src.auth.dependencies import get_current_user
from src.models.user import User

from src.retrieval.retriever import retrieve_chunks
from src.services.query_betterment import (
    QueryBettermentPipeline,
    ConversationTurn,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Singleton Query Betterment Pipeline
_qb_pipeline = QueryBettermentPipeline()

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    question: str
    history: Optional[list[ConversationTurn]] = None
    debug: bool = False


@router.post("/chat")
async def chat(request: ChatRequest , current_user: User = Depends(get_current_user)):

    # ---------------- Query Betterment ---------------- #

    qb_result = _qb_pipeline.run(
        query=request.question,
        history=request.history,
        debug_mode=request.debug,
    )

    # ---------------- Retrieve Context ---------------- #

    chunks = retrieve_chunks(qb_result.final_query)

    # ============================================================
    # CASE 1: No Chunks Found → Gemini answers from own knowledge
    # ============================================================

    if not chunks:

        prompt = f"""
You are an expert Enterprise AI Assistant.

Answer the user's question using your own reliable knowledge.

Instructions:

- Never mention:
    - Knowledge Base
    - Documents
    - Proposals
    - Context
    - RAG
    - Retrieval
    - Internal Search

- Never say:
    - I couldn't find the information.
    - No relevant documents were found.
    - The proposal doesn't contain this.

- If you know the answer, answer confidently.

- If the question requires confidential or impossible-to-know information,
  politely explain that the exact information cannot be confirmed and provide
  the best general guidance.

- Use Markdown formatting when appropriate.

User Question:

{request.question}

Answer:
"""

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )

        result = {
            "answer": response.text.strip()
        }

    # ============================================================
    # CASE 2: Chunks Found → Use RAG
    # ============================================================

    else:

        context = "\n\n".join(
            [
                f"[From: {c['document_name']}]\n{c['text']}"
                for c in chunks
            ]
        )

        prompt = f"""
You are an expert Enterprise AI Assistant.

Use the provided context as the primary source of truth.

Instructions:

- If the context answers the question, answer from it.

- If the context is incomplete, supplement it with your own reliable
  general knowledge.

- Never mention:
    - Context
    - Documents
    - RAG
    - Retrieval
    - Knowledge Base
    - Proposals

- Never fabricate confidential information.

Context:

{context}

User Question:

{request.question}

Answer:
"""

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )

        result = {
            "answer": response.text.strip()
        }

    # ---------------- Debug Response ---------------- #

    if request.debug:

        result["query_betterment"] = {
            "original_query": qb_result.original_query,
            "final_query": qb_result.final_query,
            "all_queries": qb_result.all_queries,
            "intent": qb_result.intent.model_dump() if qb_result.intent else None,
            "keywords": qb_result.keywords.model_dump() if qb_result.keywords else None,
            "overall_confidence": qb_result.overall_confidence,
            "total_latency_ms": qb_result.total_latency_ms,
            "stages": [
                t.model_dump()
                for t in qb_result.debug.traces
            ] if qb_result.debug else [],
        }

    return result