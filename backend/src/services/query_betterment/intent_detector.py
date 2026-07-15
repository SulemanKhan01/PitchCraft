"""
intent_detector.py — Stage 2: Classify the semantic intent of the query
into one of 13 well-defined categories.

Responsibility (SRP):
  ONLY classify intent. Does not modify the query text.

Intent taxonomy:
  question       — User wants a direct factual answer
  search         — User wants to find documents or information
  comparison     — User wants to compare two or more things
  definition     — User wants to understand what something means
  summarization  — User wants a summary or overview
  debugging      — User has an error or bug to resolve
  programming    — User wants code, implementation, or dev help
  documentation  — User wants API references, specs, or docs
  how_to         — User wants step-by-step instructions
  conversation   — Small talk or general statement
  follow_up      — Continuation of a previous question
  classification — User wants something categorized or labelled
  unknown        — Cannot be classified with confidence
"""
from __future__ import annotations

import logging

from .models import IntentResult, IntentType
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.intent_detector")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:IntentDetector] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

# ─────────────────────────────────────────────────────────────────────────────
# Valid intent set (pre-computed for fast membership tests)
# ─────────────────────────────────────────────────────────────────────────────

_VALID_INTENTS: frozenset[str] = frozenset(i.value for i in IntentType)


# ─────────────────────────────────────────────────────────────────────────────
# IntentDetector
# ─────────────────────────────────────────────────────────────────────────────

class IntentDetector:
    """
    Stage 2 — Detects query intent from a 13-class taxonomy.

    The detected intent is passed to downstream stages (QueryRewriter,
    QueryExpander, MultiQueryGenerator) to guide their behaviour.

    Fallback: IntentType.SEARCH at confidence=0.5 on any failure.
    """

    STAGE_NAME: str = "intent_detector"

    _PROMPT_TEMPLATE: str = """\
You are a Query Intent Classifier for a technical Retrieval-Augmented Generation system.

Classify the intent of the query into EXACTLY ONE of the following categories:
{intent_list}

Category Definitions:
  question       — The user wants a direct factual answer.
  search         — The user wants to find documents, files, or stored information.
  comparison     — The user wants to compare two or more things.
  definition     — The user wants to know what something means or how it works.
  summarization  — The user wants a summary, overview, or key points.
  debugging      — The user has an error, exception, or bug to resolve.
  programming    — The user wants code, implementation details, or dev guidance.
  documentation  — The user is looking for API references, specs, or official docs.
  how_to         — The user wants step-by-step instructions or a tutorial.
  conversation   — The user is making small talk or a general statement.
  follow_up      — The user is asking a follow-up to a previous question.
  classification — The user wants something categorized, labeled, or grouped.
  unknown        — The intent cannot be determined with confidence.

Rules:
  1. Choose EXACTLY ONE category from the list above.
  2. Use the exact string value (e.g. "debugging", not "Debugging").
  3. Optionally provide a brief sub_intent qualifier (e.g. "runtime error",
     "performance comparison", "installation guide").
  4. Return ONLY a valid JSON object — no prose, no markdown:
     {{
       "intent": "<exact category string>",
       "sub_intent": "<optional brief qualifier or null>",
       "confidence": <0.0–1.0 float>
     }}

Query: "{query}"

JSON Response:"""

    def detect(self, text: str) -> IntentResult:
        """
        Classify the semantic intent of the query.

        Args:
            text: Spell-corrected query from Stage 1.

        Returns:
            IntentResult. Falls back to SEARCH at confidence=0.5 on failure.
        """
        intent_list = ", ".join(sorted(_VALID_INTENTS))
        prompt      = self._PROMPT_TEMPLATE.format(
            intent_list=intent_list, query=text
        )

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "intent" in data:
                raw_intent = str(data["intent"]).strip().lower()

                # Sanitise: unknown intent string → IntentType.UNKNOWN
                if raw_intent not in _VALID_INTENTS:
                    logger.warning(
                        "LLM returned unknown intent '%s'; mapping to 'unknown'.",
                        raw_intent,
                    )
                    raw_intent = IntentType.UNKNOWN.value

                intent     = IntentType(raw_intent)
                sub_intent = data.get("sub_intent") or None
                confidence = float(data.get("confidence", 0.85))

                logger.info(
                    "Intent=%s sub=%s conf=%.2f | %.0f ms",
                    intent.value, sub_intent, confidence, t["elapsed_ms"],
                )
                return IntentResult(
                    intent=intent,
                    sub_intent=sub_intent,
                    confidence=confidence,
                )

            logger.warning(
                "Unexpected LLM response format; defaulting to SEARCH. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Intent detection failed (%s: %s); defaulting to SEARCH.",
                type(exc).__name__, exc,
            )

        return IntentResult(intent=IntentType.SEARCH, confidence=0.5)
