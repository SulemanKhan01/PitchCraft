"""
spell_corrector.py — Stage 1: Fix typographical, OCR, grammar, and keyboard
errors in the user query without altering its intent.

Responsibility (SRP):
  ONLY correct surface-level text errors. Never change meaning, add new
  information, or rephrase for style.

Covers:
  - Typographical errors       (teh → the, recieve → receive)
  - OCR errors                 (0 for O, 1 for l, rn for m)
  - Keyboard mistakes          (adjacent key presses: tge → the)
  - Missing words              (How do I in Python → How do I do X in Python)
  - Grammar errors             (subject-verb agreement, tense)
  - Punctuation correction     (missing apostrophes, stray commas)
"""
from __future__ import annotations

import logging

from .models import SpellCorrectionResult
from .utils  import get_gemini_client, timer, parse_json_from_llm, GEMINI_FLASH_LITE

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.spell_corrector")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:SpellCorrector] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# SpellCorrector
# ─────────────────────────────────────────────────────────────────────────────

class SpellCorrector:
    """
    Stage 1 — Corrects surface-level text errors using an LLM.

    Strategy:
      - LLM primary (handles technical vocabulary, context-aware corrections)
      - Graceful fallback: returns the original query unchanged on any failure

    Never modifies:
      - Technical terms, library names, model names, error codes
      - Proper nouns (company names, product names)
      - Version strings (v2.0, 3.10.0)
      - File names and paths
    """

    STAGE_NAME: str = "spell_corrector"

    _PROMPT_TEMPLATE: str = """\
You are a Spelling and Grammar Corrector for a technical search system.

Correct ALL errors in the query below. Fix:
  • Typographical errors        (teh → the, recieve → receive)
  • OCR errors                  (0 for O, 1 for l, rn for m)
  • Keyboard mistakes           (adjacent-key typos: tge → the)
  • Missing or duplicated words
  • Basic grammar errors        (subject-verb agreement, wrong tense)
  • Punctuation issues          (missing apostrophes, stray commas)

Rules:
  1. Do NOT change the meaning or intent of the query.
  2. Do NOT add new information.
  3. Preserve ALL technical terms, library names, model names, error codes,
     version strings, proper nouns, and file names EXACTLY as written.
  4. If the query is already correct, return it UNCHANGED.
  5. Return ONLY a valid JSON object — no prose, no markdown fences:
     {{
       "corrected": "<corrected query string>",
       "changes": ["<what was fixed and why>", ...],
       "confidence": <0.0–1.0 float>
     }}
  6. "confidence" reflects how certain you are the corrections are right
     (1.0 = no changes needed or very confident; lower = ambiguous corrections).

Query: "{query}"

JSON Response:"""

    def correct(self, text: str) -> SpellCorrectionResult:
        """
        Correct spelling and grammar in the query.

        Args:
            text: Raw or context-resolved query string.

        Returns:
            SpellCorrectionResult. On failure, corrected=original, confidence=1.0.
        """
        if not text or not text.strip():
            return SpellCorrectionResult(
                original=text, corrected=text, changes=[], confidence=1.0
            )

        prompt = self._PROMPT_TEMPLATE.format(query=text)

        try:
            client = get_gemini_client()
            with timer() as t:
                response = client.models.generate_content(
                    model=GEMINI_FLASH_LITE,
                    contents=prompt,
                )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict) and "corrected" in data:
                corrected  = str(data["corrected"]).strip() or text
                changes    = data.get("changes", [])
                confidence = float(data.get("confidence", 0.9))

                if not isinstance(changes, list):
                    changes = []

                logger.info(
                    "'%s' → '%s' | changes=%d | conf=%.2f | %.0f ms",
                    text[:80], corrected[:80], len(changes), confidence, t["elapsed_ms"],
                )
                return SpellCorrectionResult(
                    original=text,
                    corrected=corrected,
                    changes=changes,
                    confidence=confidence,
                )

            logger.warning(
                "Unexpected LLM response format; returning original. Raw: %s",
                response.text[:200],
            )

        except Exception as exc:
            logger.warning(
                "Spell correction failed (%s: %s); returning original.",
                type(exc).__name__, exc,
            )

        return SpellCorrectionResult(
            original=text,
            corrected=text,
            changes=[],
            confidence=1.0,
        )
