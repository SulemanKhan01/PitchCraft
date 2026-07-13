"""
keyword_extractor.py — Stage 6: Extract named entities and technical terms
from the query into structured, categorised keyword lists.

Responsibility (SRP):
  ONLY extract and categorise keywords. Does not modify the query text.

Extraction categories:
  entities    — Named entities (companies, products, projects, people)
  frameworks  — Frameworks and libraries (React, FastAPI, LangChain, etc.)
  languages   — Programming/query languages (Python, SQL, JavaScript, etc.)
  errors      — Error types, exception names, HTTP codes (ImportError, 404)
  tools       — Developer tools, CLIs, platforms (Docker, Git, Kubernetes)
  models      — AI/ML model identifiers (GPT-4, BERT, gemini-2.0, YOLOv8)
  file_names  — Specific file or path references (config.py, .env)
  versions    — Version strings or release identifiers (v2.0, 3.10, 2024-01)
  keywords    — Any other important domain-specific nouns or technical terms

These keywords are appended to the final query to maximise recall for
documents that contain the exact technical identifiers the user mentioned.
"""
from __future__ import annotations

import logging

from .models import KeywordResult
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.keyword_extractor")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:KeywordExtractor] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

# ─────────────────────────────────────────────────────────────────────────────
# Fields that map 1-to-1 to KeywordResult (used for sanitisation)
# ─────────────────────────────────────────────────────────────────────────────

_KW_FIELDS: tuple[str, ...] = (
    "entities", "frameworks", "languages", "errors",
    "tools", "models", "file_names", "versions", "keywords",
)


# ─────────────────────────────────────────────────────────────────────────────
# KeywordExtractor
# ─────────────────────────────────────────────────────────────────────────────

class KeywordExtractor:
    """
    Stage 6 — Technical Named Entity Recognition tuned for developer queries.

    Extracts structured keyword categories that are:
      1. Appended to the final query string for richer embedding representation
      2. Returned in QueryBettermentResult.keywords for downstream use
         (e.g., metadata filtering, faceted search)

    Fallback: returns an empty KeywordResult with confidence=0.5 on failure.
    """

    STAGE_NAME: str = "keyword_extractor"

    _PROMPT_TEMPLATE: str = """\
You are a Technical Named Entity Recognizer (NER) for a RAG retrieval system.

Extract ALL technical entities from the query below and classify them into
the following categories. Use empty lists [] for categories with no matches.

Categories:
  entities   — Named entities: company names, product names, project names, people
  frameworks — Frameworks and libraries: React, FastAPI, LangChain, TensorFlow, Qdrant
  languages  — Programming/query languages: Python, JavaScript, SQL, Go, Rust
  errors     — Errors, exceptions, HTTP codes: ImportError, 404, NullPointerException
  tools      — Developer tools, CLIs, platforms: Docker, Git, Kubernetes, VS Code
  models     — AI/ML model names: GPT-4, BERT, gemini-embedding-2, YOLOv8, Llama-3
  file_names — File names or paths: config.py, .env, requirements.txt, /data/raw/
  versions   — Version numbers / dates: v2.0, 3.10.0, 2024-01, Python 3.11
  keywords   — Other important domain-specific technical nouns not covered above

Rules:
  1. Extract ONLY terms present or strongly implied by the query.
  2. Do NOT invent terms or add general synonyms (that is a different stage).
  3. Each term should be a short, exact string (e.g. "FastAPI", not "FastAPI framework").
  4. Return ONLY a valid JSON object — no prose, no markdown fences:
     {{
       "entities":   [],
       "frameworks": [],
       "languages":  [],
       "errors":     [],
       "tools":      [],
       "models":     [],
       "file_names": [],
       "versions":   [],
       "keywords":   [],
       "confidence": <0.0–1.0 float>
     }}

Query: "{query}"

JSON Response:"""

    def extract(self, text: str) -> KeywordResult:
        """
        Extract and categorise technical keywords from the query.

        Args:
            text: Expanded query from Stage 4 (richest form of the query).

        Returns:
            KeywordResult with categorised keyword lists.
            Returns an empty KeywordResult on failure.
        """
        prompt = self._PROMPT_TEMPLATE.format(query=text)

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict):
                confidence = float(data.get("confidence", 0.85))

                # Sanitise: ensure every field is a clean list of strings
                cleaned: dict[str, list[str]] = {}
                for field in _KW_FIELDS:
                    raw = data.get(field, [])
                    if isinstance(raw, list):
                        cleaned[field] = [str(v).strip() for v in raw if str(v).strip()]
                    else:
                        cleaned[field] = []

                result = KeywordResult(confidence=confidence, **cleaned)
                total  = len(result.all_keywords())

                logger.info(
                    "Extracted %d keywords across %d categories | conf=%.2f | %.0f ms",
                    total, len(_KW_FIELDS), confidence, t["elapsed_ms"],
                )
                return result

            logger.warning(
                "Unexpected LLM response; returning empty keywords. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Keyword extraction failed (%s: %s); returning empty result.",
                type(exc).__name__, exc,
            )

        return KeywordResult(confidence=0.5)
