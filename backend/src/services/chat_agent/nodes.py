"""
nodes.py — Node execution steps for RAG Chat Agent workflow.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from src.retrieval.retriever import retrieve_chunks
from src.services.web_search import search_web, format_web_results_as_context
from src.services.query_betterment import QueryBettermentPipeline
from src.config import GEMINI_MODEL
from .state import ChatAgentState

load_dotenv()
logger = logging.getLogger("chat_agent.nodes")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [ChatAgent:Nodes] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_qb_pipeline = QueryBettermentPipeline()
SCORE_THRESHOLD = 0.60


def query_betterment_node(state: ChatAgentState) -> Dict[str, Any]:
    """Node 1: Optimize query using history & intention analysis."""
    logger.info("[Node 1/4: query_betterment] Running Query Betterment pipeline...")
    try:
        qb_res = _qb_pipeline.run(
            query=state["question"],
            history=state.get("history"),
            debug_mode=state.get("debug_mode", False),
        )
        logger.info(f"[Node 1/4: query_betterment] Final query: '{qb_res.final_query}'")
        return {"qb_result": qb_res}
    except Exception as exc:
        logger.error(f"[Node 1/4: query_betterment] Failed: {exc}")
        return {"qb_result": None}


def retrieve_context_node(state: ChatAgentState) -> Dict[str, Any]:
    """Node 2: Search Qdrant vector database for relevant proposal chunks."""
    logger.info("[Node 2/4: retrieve_context] Searching Qdrant vector store...")
    try:
        query_text = state["question"]
        raw_chunks = retrieve_chunks(query_text)
        valid_chunks = [c for c in raw_chunks if c.get("score", 0) >= SCORE_THRESHOLD]

        logger.info(f"[Node 2/4: retrieve_context] {len(raw_chunks)} raw chunks found -> {len(valid_chunks)} above threshold {SCORE_THRESHOLD}")
        return {"raw_chunks": raw_chunks, "chunks": valid_chunks}
    except Exception as exc:
        logger.error(f"[Node 2/4: retrieve_context] Retrieval failed: {exc}")
        return {"raw_chunks": [], "chunks": [], "error": str(exc)}


def web_search_fallback_node(state: ChatAgentState) -> Dict[str, Any]:
    """Node 3 (Fallback): Triggered when Qdrant chunks are below threshold."""
    logger.info("[Node 3/4: web_search_fallback] No vector chunks found. Running Tavily Web Search...")
    try:
        web_results = search_web(state["question"], max_results=5)
        web_context = format_web_results_as_context(web_results)
        used = bool(web_context)
        logger.info(f"[Node 3/4: web_search_fallback] Web results found: {used}")
        return {"web_context": web_context, "use_web_search": used}
    except Exception as exc:
        logger.error(f"[Node 3/4: web_search_fallback] Search failed: {exc}")
        return {"web_context": "", "use_web_search": False}


def generate_answer_node(state: ChatAgentState) -> Dict[str, Any]:
    """Node 4: Constructs appropriate prompt (RAG vs Web vs Knowledge) and calls Gemini."""
    logger.info("[Node 4/4: generate_answer] Calling Gemini LLM...")
    chunks = state.get("chunks") or []
    web_context = state.get("web_context") or ""
    question = state["question"]
    prev_id = state.get("previous_interaction_id")

    # Construct Prompt & Determine Source
    if chunks:
        source = "rag"
        context_str = "\n\n".join([f"[From: {c['document_name']}]\n{c['text']}" for c in chunks])
        prompt = f"""You are an expert Enterprise AI Assistant. Use the provided context as primary source of truth.
        Instructions:
        - If context answers question, answer from it. Supplement with reliable knowledge if incomplete.
        - Never mention: Context, Documents, RAG, Retrieval, Knowledge Base, Proposals.
        
        Context:
        {context_str}
        
        User Question:
        {question}
        
        Answer:"""
    elif web_context:
        source = "web_search"
        prompt = f"""You are an expert Enterprise AI Assistant. Use the web search results below as primary source.
        Instructions:
        - Answer based on web search results provided. Cite source URL naturally.
        - Never mention: RAG, Retrieval, Knowledge Base, Vector DB.
        
        {web_context}
        
        User Question:
        {question}
        
        Answer:"""
    else:
        source = "gemini_knowledge"
        prompt = f"""You are an expert Enterprise AI Assistant. Answer using your own reliable knowledge.
        Instructions:
        - Never mention: Knowledge Base, Documents, RAG, Context.
        
        User Question:
        {question}
        
        Answer:"""

    # Call Gemini Interaction API
    kwargs = {"model": GEMINI_MODEL, "input": prompt}
    if prev_id and prev_id.strip():
        kwargs["previous_interaction_id"] = prev_id.strip()

    try:
        interaction = _client.interactions.create(**kwargs)
    except Exception:
        kwargs.pop("previous_interaction_id", None)
        interaction = _client.interactions.create(**kwargs)

    ans_text = interaction.output_text.strip() if hasattr(interaction, "output_text") and interaction.output_text else ""
    logger.info(f"[Node 4/4: generate_answer] Done — Source: '{source}', Interaction ID: '{interaction.id}'")

    return {
        "answer_text": ans_text,
        "interaction_id": interaction.id,
        "source": source,
    }
