"""
web_search.py — Tavily web search service for PitchCraft.

Used as a fallback when no relevant chunks are found in Qdrant.
Searches the web and returns formatted context for Gemini to use.
"""

import os
import logging
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

logger = logging.getLogger("web_search")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [WebSearch] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

# Singleton Tavily client
_tavily_client = None


def _get_tavily_client() -> TavilyClient:
    """Return a shared Tavily client (lazy singleton)."""
    global _tavily_client
    if _tavily_client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "TAVILY_API_KEY is not set. Add it to your .env file."
            )
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using Tavily and return structured results.

    Args:
        query:       The search query string.
        max_results: Number of results to return (default 5).

    Returns:
        List of dicts, each with keys:
            - 'title':   Page title
            - 'url':     Source URL
            - 'content': Relevant snippet/excerpt
    """
    try:
        client = _get_tavily_client()
        logger.info("Searching web for: '%s'", query[:80])

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",       # "basic" is fast; use "advanced" for deeper results
            include_answer=False,       # We'll let Gemini answer, not Tavily
            include_raw_content=False,  # Snippets only — keeps context concise
        )

        results = response.get("results", [])
        logger.info("Found %d web results.", len(results))

        formatted = []
        for r in results:
            formatted.append({
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", ""),
            })

        return formatted

    except Exception as exc:
        logger.error("Web search failed (%s: %s). Returning empty results.", type(exc).__name__, exc)
        return []


def format_web_results_as_context(results: list[dict]) -> str:
    """
    Format Tavily results into a clean context string for Gemini.

    Args:
        results: List of dicts from search_web().

    Returns:
        A formatted multi-line string ready to inject into a prompt.
    """
    if not results:
        return ""

    lines = ["Web Search Results:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"Source: {r['url']}")
        lines.append(f"{r['content']}")
        lines.append("")  # blank line between results

    return "\n".join(lines)
