"""
query_expander.py — Stage 4: Expand the rewritten query with synonyms,
aliases, technical terms, abbreviations, related concepts, and framework names.

Responsibility (SRP):
  ONLY expand the query's vocabulary to improve retrieval recall.
  Does not rewrite or restructure the query (that is Stage 3's job).

Expansion categories:
  - Synonyms        (bug → error, issue, defect)
  - Abbreviations   (ML → Machine Learning, API → Application Programming Interface)
  - Full forms      (CNN → Convolutional Neural Network)
  - Related frameworks/libraries (Python web framework → Django, Flask, FastAPI)
  - Technical aliases  (vector database → Qdrant, Pinecone, Weaviate, ChromaDB)
  - Related concepts   (RAG → embeddings, vector search, semantic retrieval)
"""
from __future__ import annotations

import logging

from .models import ExpansionResult, IntentType
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.query_expander")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:QueryExpander] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# QueryExpander
# ─────────────────────────────────────────────────────────────────────────────

class QueryExpander:
    """
    Stage 4 — Vocabulary expansion for improved retrieval recall.

    Appends 3-8 semantically related terms to the rewritten query.
    Falls back to the original query unchanged on any failure.
    """

    STAGE_NAME: str = "query_expander"

    _PROMPT_TEMPLATE: str = """\
You are a Technical Query Expander for a production RAG retrieval system.

Expand the query by identifying related terms that should be included to improve
retrieval recall (finding more relevant documents).

Types of terms to add (only include truly relevant ones):
  • Synonyms                  (bug → error, issue, defect, fault)
  • Abbreviations / full forms (ML → Machine Learning; CNN → Convolutional Neural Network)
  • Related framework names    (Python web → Django, Flask, FastAPI, Starlette)
  • Technical aliases          (vector DB → Qdrant, Pinecone, ChromaDB, Weaviate)
  • Related concepts           (RAG → embeddings, semantic search, vector retrieval)
  • Common misspellings        (if the query topic is often misspelled)

Rules:
  1. Only add terms that are GENUINELY relevant — do NOT hallucinate or pad.
  2. Preserve the original query text intact in "final_query".
  3. Limit expanded_terms to 3–8 most impactful terms.
  4. Do NOT duplicate terms already present in the query.
  5. Intent context: {intent} — use this to focus the expansion.
  6. Return ONLY a valid JSON object — no prose, no markdown:
     {{
       "expanded_terms": ["<term1>", "<term2>", ...],
       "final_query": "<original query> <expanded terms joined by single space>",
       "confidence": <0.0–1.0 float>
     }}

Query: "{query}"

JSON Response:"""

    def expand(self, text: str, intent: IntentType) -> ExpansionResult:
        """
        Expand the query vocabulary for better retrieval recall.

        Args:
            text:   Rewritten query from Stage 3.
            intent: Classified intent from Stage 2 (used to focus expansion).

        Returns:
            ExpansionResult with the expanded query and term list.
            Falls back to original query on failure.
        """
        prompt = self._PROMPT_TEMPLATE.format(intent=intent.value, query=text)

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "final_query" in data:
                expanded_terms = data.get("expanded_terms", [])
                final_query    = str(data["final_query"]).strip() or text
                confidence     = float(data.get("confidence", 0.85))

                if not isinstance(expanded_terms, list):
                    expanded_terms = []

                logger.info(
                    "Added %d expansion terms | conf=%.2f | %.0f ms",
                    len(expanded_terms), confidence, t["elapsed_ms"],
                )
                return ExpansionResult(
                    original=text,
                    expanded_terms=expanded_terms,
                    final_query=final_query,
                    confidence=confidence,
                )

            logger.warning(
                "Unexpected LLM response; returning original. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Query expansion failed (%s: %s); returning original.",
                type(exc).__name__, exc,
            )

        return ExpansionResult(
            original=text,
            expanded_terms=[],
            final_query=text,
            confidence=0.7,
        )
