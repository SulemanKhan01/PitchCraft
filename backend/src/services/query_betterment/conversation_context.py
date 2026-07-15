"""
conversation_context.py — Resolves pronouns and elliptical references in
follow-up queries using the conversation history.

Responsibility (SRP):
  ONLY substitute context-dependent references so that the query is fully
  self-contained before any other stage processes it.

Examples:
  History:  "What are the features of the Edge-CV Pipeline proposal?"
  Query:    "What about the second one?"
  Resolved: "What are the features of the second Edge-CV Pipeline proposal?"
"""
from __future__ import annotations

import logging
from typing import Optional

from .models import ConversationTurn
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.conversation_context")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:ConversationContext] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_MAX_HISTORY_TURNS: int = 6   # only use the most recent N turns to keep the prompt concise


# ─────────────────────────────────────────────────────────────────────────────
# ConversationContext
# ─────────────────────────────────────────────────────────────────────────────

class ConversationContext:
    """
    Phase 0 support module — resolves follow-up queries against conversation history.

    If no history is provided the query is returned unchanged with confidence=1.0.
    Failures degrade gracefully: original query is returned, pipeline continues.
    """

    STAGE_NAME: str = "conversation_context"

    _PROMPT_TEMPLATE: str = """\
You are a Query Context Resolver for a retrieval system.

Given the CONVERSATION HISTORY and the CURRENT QUERY, rewrite the query as a
fully self-contained sentence that can be understood without the history.

Rules:
1. Replace ALL pronouns (it, they, this, that, these, those, he, she) with the
   explicit entity they refer to.
2. Expand ALL elliptical references ("the second one", "that approach",
   "the error above") into explicit phrases.
3. If the query is already self-contained, return it UNCHANGED.
4. Do NOT add new information that is not present in the history.
5. Do NOT answer the question — only rewrite it.
6. Return ONLY a valid JSON object — no prose, no markdown:
   {{"resolved_query": "<string>", "confidence": <0.0–1.0>}}

CONVERSATION HISTORY (most recent {n} turns):
{history}

CURRENT QUERY: {query}

JSON Response:"""

    def resolve(
        self,
        query:   str,
        history: Optional[list[ConversationTurn]] = None,
    ) -> tuple[str, float]:
        """
        Resolve pronouns and references in the query using the conversation history.

        Args:
            query:   The raw user query (possibly context-dependent).
            history: List of previous ConversationTurn objects.

        Returns:
            (resolved_query: str, confidence: float)
            Falls back to (query, 1.0) on any error.
        """
        if not history:
            logger.debug("No history provided — skipping context resolution.")
            return query, 1.0

        # Build a readable history block from the most recent turns
        recent = history[-_MAX_HISTORY_TURNS:]
        history_text = "\n".join(
            f"{turn.role.upper()}: {turn.content}" for turn in recent
        )

        prompt = self._PROMPT_TEMPLATE.format(
            n=len(recent),
            history=history_text,
            query=query,
        )

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "resolved_query" in data:
                resolved   = str(data["resolved_query"]).strip() or query
                confidence = float(data.get("confidence", 0.85))
                logger.info(
                    "Resolved '%s' → '%s' (conf=%.2f, %.0f ms)",
                    query[:80], resolved[:80], confidence, t["elapsed_ms"],
                )
                return resolved, confidence

            logger.warning(
                "LLM returned unexpected format for context resolution; "
                "using original query. Raw: %s", response.text[:200]
            )

        except Exception as exc:
            logger.warning(
                "Context resolution failed (%s: %s); using original query.",
                type(exc).__name__, exc,
            )

        return query, 1.0
