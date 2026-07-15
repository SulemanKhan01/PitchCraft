"""
query_rewriter.py — Stage 3: Convert ambiguous or vague queries into
retrieval-friendly, explicit, self-contained queries.

Responsibility (SRP):
  ONLY rewrite the query for retrieval precision.
  Does not expand vocabulary (that is Stage 4's job).

The detected intent from Stage 2 is used to select a rewriting strategy
that matches the user's actual need.
"""
from __future__ import annotations

import logging

from .models import RewriteResult, IntentType
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.query_rewriter")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:QueryRewriter] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# Intent → rewriting strategy map
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_GUIDANCE: dict[IntentType, str] = {
    IntentType.DEBUGGING:     (
        "Frame as: 'How to fix [specific error/exception] when [context]?' "
        "Include the error name and the surrounding action."
    ),
    IntentType.COMPARISON:    (
        "Frame as: 'Compare [A] vs [B] in terms of [specific aspect].' "
        "Make both subjects and the comparison dimension explicit."
    ),
    IntentType.HOW_TO:        (
        "Frame as: 'Step-by-step guide to [specific task] in [context/language/tool].' "
        "Include all implied context."
    ),
    IntentType.DEFINITION:    (
        "Frame as: 'What is [term], how does it work, and when is it used?' "
        "Spell out the full term if an abbreviation is used."
    ),
    IntentType.SUMMARIZATION: (
        "Frame as: 'Summarize [topic/document] covering [key aspects].' "
        "Make the subject and desired coverage explicit."
    ),
    IntentType.PROGRAMMING:   (
        "Include the programming language, framework, and the specific task. "
        "Frame as: 'How to [task] in [language/framework] using [tool/library]?'"
    ),
    IntentType.DOCUMENTATION: (
        "Frame as: 'Official documentation or API reference for [function/class/module] "
        "in [library/version].' Include the exact symbol and library."
    ),
    IntentType.SEARCH:        (
        "Make the search target explicit: name the document, topic, or entity "
        "the user is looking for. Remove vague qualifiers."
    ),
    IntentType.QUESTION:      (
        "Phrase as a direct, specific question. Include all implicit context "
        "so the question is answerable without further clarification."
    ),
    IntentType.CLASSIFICATION: (
        "Frame as: 'Classify/categorize [item] as [taxonomy/criteria].' "
        "State the classification criteria explicitly."
    ),
}

_DEFAULT_GUIDANCE: str = (
    "Make the query explicit, specific, and self-contained. "
    "Remove vague pronouns. Add implied domain context."
)


# ─────────────────────────────────────────────────────────────────────────────
# QueryRewriter
# ─────────────────────────────────────────────────────────────────────────────

class QueryRewriter:
    """
    Stage 3 — Rewrites queries to maximise retrieval precision.

    Uses the intent detected in Stage 2 to choose a targeted rewriting style.
    Fallback: returns the original query unchanged on any failure.
    """

    STAGE_NAME: str = "query_rewriter"

    _PROMPT_TEMPLATE: str = """\
You are a Query Rewriter for a production RAG (Retrieval-Augmented Generation) system.

Your task is to rewrite the query so it is maximally effective for dense embedding search.

Detected Intent: {intent}
Rewriting Guidance: {guidance}

Rewriting Rules:
  1. Make the query explicit and fully self-contained.
  2. Remove ambiguity and vague pronouns (it, this, that, they).
  3. Add domain context that is implied but not stated (e.g., "Python" if obvious).
  4. Do NOT fabricate facts or add information not implied by the query.
  5. Keep the rewritten query concise (ideally under 60 words).
  6. Preserve all technical terms, library names, error codes, and proper nouns exactly.
  7. Return ONLY a valid JSON object — no prose, no markdown fences:
     {{
       "rewritten": "<rewritten query>",
       "rationale": "<one-sentence explanation of what changed and why>",
       "confidence": <0.0–1.0 float>
     }}

Original Query: "{query}"

JSON Response:"""

    def rewrite(self, text: str, intent: IntentType) -> RewriteResult:
        """
        Rewrite the query for optimal retrieval based on its intent.

        Args:
            text:   Spell-corrected query from Stage 1.
            intent: Classified intent from Stage 2.

        Returns:
            RewriteResult. Falls back to original query on failure.
        """
        guidance = _INTENT_GUIDANCE.get(intent, _DEFAULT_GUIDANCE)
        prompt   = self._PROMPT_TEMPLATE.format(
            intent=intent.value, guidance=guidance, query=text
        )

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "rewritten" in data:
                rewritten  = str(data["rewritten"]).strip() or text
                rationale  = str(data.get("rationale", "")).strip()
                confidence = float(data.get("confidence", 0.85))

                logger.info(
                    "'%s' → '%s' | conf=%.2f | %.0f ms",
                    text[:80], rewritten[:80], confidence, t["elapsed_ms"],
                )
                return RewriteResult(
                    original=text,
                    rewritten=rewritten,
                    rationale=rationale,
                    confidence=confidence,
                )

            logger.warning(
                "Unexpected LLM response; returning original. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Query rewriting failed (%s: %s); returning original.",
                type(exc).__name__, exc,
            )

        return RewriteResult(
            original=text,
            rewritten=text,
            rationale="Rewriting skipped due to error.",
            confidence=0.7,
        )
