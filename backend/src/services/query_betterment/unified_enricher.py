"""
unified_enricher.py — Single-shot Query Optimizer for PitchCraft.

Replaces 6 separate LLM roundtrips with 1 Master Prompt that performs:
1. Typo & OCR correction
2. Intent classification
3. Technical keyword extraction
4. Retrieval-friendly query rewriting
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List

from .utils import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

logger = logging.getLogger("query_betterment.unified_enricher")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [QB:UnifiedEnricher] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


class UnifiedQueryEnricher:
    """
    Executes a single master LLM call to perform complete query betterment.
    """

    STAGE_NAME: str = "unified_enricher"

    _MASTER_PROMPT: str = """\
You are an Enterprise Query Optimizer for a proposal & technical document RAG system.

Optimize the raw user query below for dense vector retrieval in ONE step.

Perform all of the following actions:
1. SPELL & OCR FIX: Fix typographical, OCR, or grammatical errors (e.g. "teh" -> "the", "0" -> "O").
2. INTENT DETECT: Classify intent into EXACTLY ONE of [question, search, comparison, definition, summarization, debugging, programming, how_to, conversation].
3. KEYWORDS & SYNONYMS: Extract key technical terms, proposal identifiers, or technologies, and include relevant domain synonyms.
4. REWRITE QUERY: Rewrite into a clean, explicit, self-contained, retrieval-optimized query string.

Rules:
- Preserve all proper nouns, product names, version numbers, and file paths exactly.
- Do NOT answer the question — only optimize the query for search.
- Return ONLY a valid JSON object — no markdown formatting outside JSON:

{{
  "corrected_query": "<string>",
  "intent": "<string>",
  "keywords": ["<string>", "..."],
  "final_query": "<string>",
  "confidence": <0.0 to 1.0 float>
}}

User Query: "{query}"

JSON Response:"""

    def enrich(self, query: str) -> Dict[str, Any]:
        """
        Execute unified query enrichment in a single Gemini API call.
        """
        if not query or not query.strip():
            return {
                "corrected_query": query,
                "intent": "search",
                "keywords": [],
                "final_query": query,
                "confidence": 1.0,
            }

        prompt = self._MASTER_PROMPT.format(query=query)

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if isinstance(data, dict) and "final_query" in data:
                final_query = str(data.get("final_query", query)).strip() or query
                intent = str(data.get("intent", "search")).strip().lower()
                keywords = data.get("keywords", [])
                confidence = float(data.get("confidence", 0.9))

                logger.info(
                    "Enriched query in %.0f ms: '%s' -> '%s' (intent=%s, conf=%.2f)",
                    t["elapsed_ms"], query[:60], final_query[:60], intent, confidence
                )

                return {
                    "corrected_query": str(data.get("corrected_query", query)),
                    "intent": intent,
                    "keywords": keywords if isinstance(keywords, list) else [],
                    "final_query": final_query,
                    "confidence": confidence,
                }

        except Exception as exc:
            logger.warning("Unified enrichment failed (%s: %s). Falling back to raw query.", type(exc).__name__, exc)

        return {
            "corrected_query": query,
            "intent": "search",
            "keywords": [],
            "final_query": query,
            "confidence": 0.5,
        }
