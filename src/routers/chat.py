import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from src.retriever import retrieve_chunks

# ── Query Betterment — pre-embedding enrichment pipeline ─────────────────────
from src.query_betterment import QueryBettermentPipeline, ConversationTurn

load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = GEMINI_API_KEY)

# Module-level singleton — constructed once, reused for every request
_qb_pipeline = QueryBettermentPipeline()


router = APIRouter(
    prefix = "/api/chat",
    tags = ["Chat"]
)

class ChatRequest(BaseModel):
    question : str
    # category_filter: str = None
    history  : Optional[list[ConversationTurn]] = None   # conversation turns for follow-up resolution
    debug    : bool = False                               # set True to receive per-stage debug trace


@router.post("/chat")
async def chat(request: ChatRequest):

    # ── Query Betterment: enrich the raw query before embedding ──────────────
    qb_result = _qb_pipeline.run(
        query      = request.question,
        history    = request.history,
        debug_mode = request.debug,
    )

    chunks = retrieve_chunks(qb_result.final_query)#,request.category_filter

    if not chunks:
        return {"answer": "I could not find any relevant information in the proposals."}



    context = "\n\n".join([f"[From: {c['document_name']}]\n{c['text']}" for c in chunks])

    prompt = f"""You are a helpful assistant for a proposal management system.
    Answer the user's question ONLY using the context provided below.
    If the answer is not found in the context, say "I don't have that information in the proposals."
    Do NOT make up any information.

    Context:
    {context}

    User Question: {request.question}

    Answer:"""

    response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
    )

    # ── Build response — include debug trace when requested ──────────────────
    result: dict = {"answer": response.text.strip()}

    if request.debug:
        result["query_betterment"] = {
            "original_query":     qb_result.original_query,
            "final_query":        qb_result.final_query,
            "all_queries":        qb_result.all_queries,
            "intent":             qb_result.intent.model_dump() if qb_result.intent else None,
            "keywords":           qb_result.keywords.model_dump() if qb_result.keywords else None,
            "overall_confidence": qb_result.overall_confidence,
            "total_latency_ms":   qb_result.total_latency_ms,
            "stages": [t.model_dump() for t in qb_result.debug.traces] if qb_result.debug else [],
        }

    return result
