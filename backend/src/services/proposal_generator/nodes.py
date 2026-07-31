"""
nodes.py — Node execution steps for Proposal Generation workflow.
"""

import logging
from typing import Dict, Any
from .state import ProposalState
from .chat_analyzer import analyze_chat
from .proposal_writer import write_proposal
from src.services.web_search import search_web, format_web_results_as_context

logger = logging.getLogger("proposal_generator.nodes")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [Proposal:Nodes] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def _build_web_query(requirements: dict) -> str:
    """Build a smart search query from extracted requirements."""
    parts = []
    if requirements.get("project_title"):
        parts.append(requirements["project_title"])
    if requirements.get("tech_stack"):
        parts.append(" ".join(requirements["tech_stack"][:3]))
    if requirements.get("industry"):
        parts.append(requirements["industry"])

    if not parts:
        return "software development project proposal cost timeline estimate"

    return f"{' '.join(parts)} development cost pricing timeline estimate 2025"


def analyze_chat_node(state: ProposalState) -> Dict[str, Any]:
    """Node 1: Extract structured requirements from conversation history."""
    logger.info("[Node 1/3: analyze_chat] Analyzing conversation history...")
    try:
        reqs = analyze_chat(state["messages"])
        logger.info(f"[Node 1/3: analyze_chat] Done — Project: '{reqs.get('project_title', 'N/A')}'")
        return {"requirements": reqs}
    except Exception as exc:
        logger.error(f"[Node 1/3: analyze_chat] Failed: {exc}")
        return {"requirements": {}, "error": f"Chat analysis failed: {str(exc)}"}


def web_search_node(state: ProposalState) -> Dict[str, Any]:
    """Node 2: Search web for current pricing/market context using Tavily."""
    if state.get("error"):
        logger.warning("[Node 2/3: web_search] Skipping web search due to prior error.")
        return {"web_context": "", "web_search_used": False}

    logger.info("[Node 2/3: web_search] Running Tavily web search...")
    try:
        reqs = state.get("requirements") or {}
        query = _build_web_query(reqs)
        logger.info(f"[Node 2/3: web_search] Query: '{query[:80]}'")
        
        results = search_web(query, max_results=5)
        context = format_web_results_as_context(results)
        used = bool(context)
        
        logger.info(f"[Node 2/3: web_search] Done — {len(results)} results found.")
        return {"web_query": query, "web_context": context, "web_search_used": used}
    except Exception as exc:
        logger.error(f"[Node 2/3: web_search] Search failed: {exc}")
        return {"web_context": "", "web_search_used": False, "error": f"Web search warning: {str(exc)}"}


def write_proposal_node(state: ProposalState) -> Dict[str, Any]:
    """Node 3: Generate the complete proposal document with Gemini."""
    logger.info("[Node 3/3: write_proposal] Generating proposal with Gemini...")
    try:
        reqs = state.get("requirements") or {}
        context = state.get("web_context") or ""
        
        content = write_proposal(requirements=reqs, web_context=context)
        logger.info(f"[Node 3/3: write_proposal] Done — {len(content)} characters generated.")
        return {"proposal_content": content}
    except Exception as exc:
        logger.error(f"[Node 3/3: write_proposal] Proposal writing failed: {exc}")
        return {"proposal_content": "", "error": f"Proposal generation failed: {str(exc)}"}
