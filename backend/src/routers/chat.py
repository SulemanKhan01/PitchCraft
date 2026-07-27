import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.services.web_search import search_web, format_web_results_as_context



from fastapi import Depends
# from src.auth.dependencies import get_current_user  # JWT — replaced by Clerk
# from src.models.user import User                    # JWT — replaced by Clerk
from src.auth.clerk_auth import get_current_user_clerk

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
    previous_interaction_id: Optional[str] = None
    history: Optional[list[ConversationTurn]] = None
    debug: bool = False


GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "howdy", "yo", "sup",
    "good morning", "good afternoon", "good evening",
    "what's up", "wasup", "whatsup",
}

def _is_greeting(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("?!.,")
    return cleaned in GREETING_WORDS or any(
        cleaned.startswith(w) for w in ("hi ", "hello ", "hey ", "good morning", "good afternoon", "good evening")
    )


@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user_clerk)):

    # ---------------- Greeting Fast-Path ---------------- #

    if _is_greeting(request.question):
        return {"answer": "Hello! How can I help you today?",
                "interaction_id": request.previous_interaction_id
        }

    # ---------------- Query Betterment ---------------- #

    qb_result = _qb_pipeline.run(
        query=request.question,
        history=request.history,
        debug_mode=request.debug,
    )

    # ---------------- Retrieve Context ---------------- #

    raw_chunks = retrieve_chunks(request.question)
    print("--- RAW CHUNKS FOUND BY QDRANT ---")
    for c in raw_chunks:
        print(f"Document: {c['document_name']} | Score: {c['score']} | Snippet: {c['text'][:100]}...")
    print("---------------------------------")

    SCORE_THRESHOLD = 0.60
    chunks = [c for c in raw_chunks if c.get("score", 0) >= SCORE_THRESHOLD]

       # ============================================================
    # CASE 1: No Chunks Found → Web Search → Gemini answers with web context
    # ============================================================

    if not chunks:

        # --- Try Tavily web search first ---
        web_results = search_web(request.question, max_results=5)
        web_context = format_web_results_as_context(web_results)

        if web_context:
            # We got web results — use them as context
            prompt = f"""
            You are an expert Enterprise AI Assistant.

            Use the web search results below as your primary source of information.

            Instructions:
            - Answer the user's question based on the web search results provided.
            - If the results are relevant, cite the source URL naturally (e.g., "According to [source]...").
            - If the web results are not relevant to the question, answer from your own reliable knowledge.
            - Use Markdown formatting when appropriate.
            - Never mention: RAG, Retrieval, Knowledge Base, Documents, Proposals, Vector DB.

            {web_context}

            User Question:

            {request.question}

            Answer:
            """
            print("**** Web search results found. Using web context. ****")

        else:
            # No web results — fall back to Gemini's own knowledge
            prompt = f"""
            You are an expert Enterprise AI Assistant.

            Answer the user's question using your own reliable knowledge.

            Instructions:
            - If you know the answer, answer confidently.
            - Use Markdown formatting when appropriate.
            - Never mention: Knowledge Base, Documents, Proposals, Context, RAG, Retrieval.
            - If the question requires confidential or impossible-to-know information,
              politely explain and provide the best general guidance.

            User Question:

            {request.question}

            Answer:
            """
            print("**** No web results found. Falling back to Gemini knowledge. ****")


        kwargs = {
            "model": "gemini-3.1-flash-lite",
            "input": prompt,
        }

        if request.previous_interaction_id and request.previous_interaction_id.strip():
            kwargs["previous_interaction_id"] = request.previous_interaction_id.strip()

        try:
            interaction = client.interactions.create(**kwargs)
        except Exception as exc:
            if "previous_interaction_id" in kwargs:
                kwargs.pop("previous_interaction_id", None)
                interaction = client.interactions.create(**kwargs)
            else:
                raise exc

        answer_text = interaction.output_text.strip() if hasattr(interaction, "output_text") and interaction.output_text else ""

        result = {
            "answer": answer_text,
            "interaction_id": interaction.id,
            "source": "web_search" if web_context else "gemini_knowledge",
        }

        print("*****************web search result****************")
        print(result)


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

        kwargs = {
            "model": "gemini-3.1-flash-lite",
            "input": prompt,
        }

        if request.previous_interaction_id and request.previous_interaction_id.strip():
            kwargs["previous_interaction_id"] = request.previous_interaction_id.strip()

        try:
            interaction = client.interactions.create(**kwargs)
        except Exception as exc:
            if "previous_interaction_id" in kwargs:
                kwargs.pop("previous_interaction_id", None)
                interaction = client.interactions.create(**kwargs)
            else:
                raise exc
        


        answer_text = interaction.output_text.strip() if hasattr(interaction, "output_text") and interaction.output_text else ""

        result = {
            "answer": answer_text,
            "interaction_id": interaction.id
        }

        print("*****************result****************")
        print(result)
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