"""
multi_query.py — Stage 5: Generate multiple semantically distinct variations
of the query to maximise retrieval recall across the embedding space.

Responsibility (SRP):
  ONLY generate query variants. Does not modify, rank, or filter results.

Why multi-query?
  A single query vector may miss relevant documents that use different
  terminology. Generating 3-5 phrasings improves coverage in embedding space.
  The orchestrator exposes all_queries for future multi-vector retrieval.
"""
from __future__ import annotations

import logging

from .models import MultiQueryResult, IntentType
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.multi_query")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:MultiQuery] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# MultiQueryGenerator
# ─────────────────────────────────────────────────────────────────────────────

class MultiQueryGenerator:
    """
    Stage 5 — Generates semantically distinct query variants.

    Each variant must:
      - Capture the same intent and information need
      - Use different vocabulary and/or sentence structure
      - Be fully self-contained and suitable for embedding

    The primary (expanded) query from Stage 4 is always the first entry.
    Generated variants are appended after it.

    Fallback: returns a list containing only the original query on failure.
    """

    STAGE_NAME: str = "multi_query"

    _PROMPT_TEMPLATE: str = """\
You are a Multi-Query Generator for a production RAG retrieval system.

Generate {n} semantically DIFFERENT phrasings of the query below.
Each phrasing must:
  • Express the SAME intent and information need
  • Use DIFFERENT vocabulary, structure, or perspective
  • Be fully self-contained (understandable without context)
  • Be suitable for dense embedding-based similarity search
  • Be concise (under 60 words each)

Variation strategies to consider:
  • Rephrase using synonyms
  • Switch from question form to declarative form (or vice versa)
  • Approach from a different angle (e.g., problem → solution, cause → effect)
  • Use more formal / more casual language
  • Expand abbreviations or contract full terms

Rules:
  1. Every variant must preserve the ORIGINAL INTENT — never drift.
  2. Do NOT copy the original query verbatim — each must be genuinely different.
  3. Return ONLY a valid JSON object — no prose, no markdown:
     {{
       "queries": ["<variant 1>", "<variant 2>", ..., "<variant {n}>"],
       "confidence": <0.0–1.0 float>
     }}

Intent: {intent}
Original Query: "{query}"

JSON Response:"""

    def __init__(self, num_queries: int = 3) -> None:
        """
        Args:
            num_queries: Number of variants to generate (default 3, max 5).
        """
        self._num_queries: int = max(1, min(num_queries, 5))

    def generate(self, text: str, intent: IntentType) -> MultiQueryResult:
        """
        Generate multiple semantic variants of the query.

        Args:
            text:   Expanded query from Stage 4.
            intent: Classified intent from Stage 2.

        Returns:
            MultiQueryResult with the list of query variants.
            Falls back to [text] on failure.
        """
        prompt = self._PROMPT_TEMPLATE.format(
            n=self._num_queries,
            intent=intent.value,
            query=text,
        )

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "queries" in data:
                raw_queries = data["queries"]

                if not isinstance(raw_queries, list):
                    raise ValueError("'queries' is not a list.")

                # Sanitise: strip empty strings
                queries = [str(q).strip() for q in raw_queries if str(q).strip()]

                if not queries:
                    queries = [text]

                confidence = float(data.get("confidence", 0.85))

                logger.info(
                    "Generated %d query variants | conf=%.2f | %.0f ms",
                    len(queries), confidence, t["elapsed_ms"],
                )
                return MultiQueryResult(queries=queries, confidence=confidence)

            logger.warning(
                "Unexpected LLM response; falling back to original. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Multi-query generation failed (%s: %s); falling back.",
                type(exc).__name__, exc,
            )

        return MultiQueryResult(queries=[text], confidence=0.6)
