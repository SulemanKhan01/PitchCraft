"""
pipeline.py — Orchestrates the full proposal generation pipeline.

Flow:
  [1] Analyze chat  → extract structured requirements (Gemini)
  [2] Web search    → get current market context (Tavily)
  [3] Write proposal → generate the full document (Gemini)
"""

import logging
from .chat_analyzer import analyze_chat
from .proposal_writer import write_proposal
from src.services.web_search import search_web, format_web_results_as_context

logger = logging.getLogger("proposal_generator.pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [ProposalPipeline] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


def _build_web_query(requirements: dict) -> str:
    """Build a smart Tavily search query from extracted requirements."""
    parts = []

    if requirements.get("project_title"):
        parts.append(requirements["project_title"])

    if requirements.get("tech_stack"):
        stack = requirements["tech_stack"]
        parts.append(" ".join(stack[:3]))  # top 3 technologies

    if requirements.get("industry"):
        parts.append(requirements["industry"])

    if not parts:
        return "software development project proposal cost timeline estimate"

    query = " ".join(parts)
    query += " development cost pricing timeline estimate 2025"
    return query


def generate_proposal(messages: list[dict]) -> dict:
    """
    Full proposal generation pipeline.

    Args:
        messages: List of {'role': 'user'|'assistant', 'content': str}
                  representing the full conversation from the DB.

    Returns:
        Dict with:
            'proposal_content'  — the generated proposal (markdown string)
            'requirements'      — extracted requirements dict
            'web_search_used'   — whether Tavily found results
    """
    logger.info("=== Proposal Generation Pipeline Started ===")
    logger.info("Input: %d messages", len(messages))

    # ── Step 1: Analyze the chat conversation ─────────────────────────────────
    logger.info("[1/3] Analyzing chat to extract requirements...")
    requirements = analyze_chat(messages)
    logger.info(
        "[1/3] Done. Project: '%s'",
        requirements.get("project_title", "N/A")
    )

    # ── Step 2: Web search for current market context ─────────────────────────
    logger.info("[2/3] Running Tavily web search...")
    web_query = _build_web_query(requirements)
    logger.info("      Query: '%s'", web_query[:80])

    web_results = search_web(web_query, max_results=5)
    web_context = format_web_results_as_context(web_results)
    web_used = bool(web_context)
    logger.info("[2/3] Done. Web results: %d found.", len(web_results))

    # ── Step 3: Generate the proposal ─────────────────────────────────────────
    logger.info("[3/3] Generating proposal with Gemini...")
    proposal_content = write_proposal(
        requirements=requirements,
        web_context=web_context,
    )
    logger.info("[3/3] Done. %d characters generated.", len(proposal_content))
    logger.info("=== Proposal Generation Pipeline Completed ===")

    return {
        "proposal_content": proposal_content,
        "requirements": requirements,
        "web_search_used": web_used,
    }
