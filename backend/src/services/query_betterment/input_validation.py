"""
input_validation.py — Input Validation module for the Query Betterment Pipeline.

Executes BEFORE every other pipeline stage.  Normalises raw user input,
rejects empty / oversized / dangerous queries, and flags prompt-injection,
SQL-injection, HTML, and JavaScript attack patterns.

Design:
  Stateless — ``validate()`` is a pure function (no side-effects beyond logging).
  Single-file — all validation logic lives here; no helper modules.
  Fail-safe  — never raises; always returns a structured ``ValidationResult``.
"""
from __future__ import annotations

import re
import logging
import unicodedata
from typing import Final

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.input_validation")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:InputValidation] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# Return model
# ─────────────────────────────────────────────────────────────────────────────

class ValidationResult(BaseModel):
    """
    Structured output of ``validate()``.

    Attributes:
        original_query:   The raw input before any modification.
        cleaned_query:    Normalised text ready for downstream stages.
        is_valid:         ``True`` when the query passes all hard validations
                          (non-empty, within length bounds, valid encoding).
        validation_errors: Human-readable list of hard failures.
        warning_flags:    Non-blocking flags for suspicious patterns
                          (injection attempts, HTML, JS, spam).
    """
    original_query:    str
    cleaned_query:     str
    is_valid:          bool
    validation_errors: list[str] = Field(default_factory=list)
    warning_flags:     list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration constants
# ─────────────────────────────────────────────────────────────────────────────

MIN_QUERY_LENGTH: Final[int] = 2
MAX_QUERY_LENGTH: Final[int] = 5_000

_MAX_REPEATED_CHARS: Final[int] = 3
_MAX_REPEATED_PUNCT: Final[int] = 3


# ─────────────────────────────────────────────────────────────────────────────
# Pattern tables (compiled once at import time)
# ─────────────────────────────────────────────────────────────────────────────

# -- Prompt-injection (case-insensitive) --

_PROMPT_INJECTION_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+|prior\s+)?instructions", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+)?(?:previous\s+|prior\s+)?instructions", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?(?:your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"show\s+(?:the\s+)?(?:your\s+)?hidden\s+prompt", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a\s+)?developer", re.IGNORECASE),
    re.compile(r"bypass\s+(?:all\s+)?safety", re.IGNORECASE),
    re.compile(r"ignore\s+(?:the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"override\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
]

# -- SQL-injection (case-insensitive) --

_SQL_INJECTION_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
    re.compile(r"\bINSERT\s+INTO\b", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+\w+\s+SET\b", re.IGNORECASE),
    re.compile(r"\bUNION\s+SELECT\b", re.IGNORECASE),
    re.compile(r"\bSELECT\s+\*\s+FROM\b", re.IGNORECASE),
    re.compile(r"\bOR\s+1\s*=\s*1\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)--", re.IGNORECASE),
    re.compile(r";\s*\w", re.IGNORECASE),
]

# -- HTML tags --

_HTML_TAG_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"<\s*script[\s>]", re.IGNORECASE),
    re.compile(r"<\s*iframe[\s>]", re.IGNORECASE),
    re.compile(r"<\s*object[\s>]", re.IGNORECASE),
    re.compile(r"<\s*embed[\s>]", re.IGNORECASE),
]

# -- JavaScript patterns --

_JS_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\beval\s*\(", re.IGNORECASE),
    re.compile(r"\bdocument\s*\.\s*cookie", re.IGNORECASE),
    re.compile(r"\bwindow\s*\.\s*location", re.IGNORECASE),
    re.compile(r"\bjavascript\s*:", re.IGNORECASE),
    re.compile(r"\bFunction\s*\(", re.IGNORECASE),
    re.compile(r"\bsetTimeout\s*\(", re.IGNORECASE),
    re.compile(r"\bsetInterval\s*\(", re.IGNORECASE),
]

# -- Repeated-character spam --

_REPEATED_CHAR_RE: Final[re.Pattern[str]] = re.compile(
    r"(.)\1{" + str(_MAX_REPEATED_CHARS) + r",}"
)

# -- Repeated-punctuation --

_REPEATED_PUNCT_RE: Final[re.Pattern[str]] = re.compile(
    r"([!?.,;:])\1{" + str(_MAX_REPEATED_PUNCT) + r",}"
)

# -- Control characters (keep \t \n \r and printable ranges) --

_CONTROL_CHAR_RE: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)

# -- Dangerous HTML tags (full removal) --

_HTML_TAG_REMOVE_RE: Final[re.Pattern[str]] = re.compile(
    r"<\s*(?:script|iframe|object|embed)\s*[^>]*>.*?</\s*(?:script|iframe|object|embed)\s*>"
    r"|<\s*(?:script|iframe|object|embed)\s*[^>]*/?>",
    re.IGNORECASE | re.DOTALL,
)

# -- Special-character spam (runs of 2+ visual-noise chars not part of words) --

_SPECIAL_CHAR_SPAM_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!\w)[@#$%^&*~]{2,}(?!\w)"
)


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_valid_utf8(raw: bytes | str) -> str:
    """
    Guarantee the input is decodable UTF-8 text.

    If *raw* is already a ``str`` it is returned as-is.
    If *raw* is ``bytes`` it is decoded; on failure an empty string is returned.
    """
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return ""


def _strip_control_characters(text: str) -> str:
    """Remove invisible ASCII control characters while preserving printable Unicode."""
    return _CONTROL_CHAR_RE.sub("", text)


def _normalize_unicode(text: str) -> str:
    """Apply NFKC normalisation (compatibility decomposition + canonical composition)."""
    return unicodedata.normalize("NFKC", text)


def _normalize_whitespace(text: str) -> str:
    """
    Collapse runs of whitespace (spaces, tabs, newlines) into a single space,
    then strip leading / trailing whitespace.
    """
    return re.sub(r"\s+", " ", text).strip()


def _normalize_repeated_characters(text: str) -> str:
    """
    Reduce excessive character repetition.

    Example: ``Hellooooooooooooo`` → ``Hellooo``
    """
    return _REPEATED_CHAR_RE.sub(lambda m: m.group(0)[: _MAX_REPEATED_CHARS], text)


def _normalize_repeated_punctuation(text: str) -> str:
    """
    Reduce runs of repeated punctuation marks to a reasonable count.

    Example: ``!!!!!!!!!!`` → ``!!!``
    """
    return _REPEATED_PUNCT_RE.sub(lambda m: m.group(0)[: _MAX_REPEATED_PUNCT], text)


def _remove_html_tags(text: str) -> str:
    """Remove dangerous HTML/XML tags (script, iframe, object, embed) entirely."""
    return _HTML_TAG_REMOVE_RE.sub("", text)


def _remove_special_char_spam(text: str) -> str:
    """
    Remove runs of 2+ visual-noise characters (@ # $ % ^ & * ~) that are not
    part of a word boundary.

    Example: ``hello @@@ world`` → ``hello  world``
    """
    return _SPECIAL_CHAR_SPAM_RE.sub("", text)


# ─────────────────────────────────────────────────────────────────────────────
# Detection helpers (non-blocking — return flag strings)
# ─────────────────────────────────────────────────────────────────────────────

def _detect_prompt_injection(text: str) -> str | None:
    """Return a flag string if a prompt-injection pattern is found, else ``None``."""
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return "prompt_injection_attempt"
    return None


def _detect_sql_injection(text: str) -> str | None:
    """Return a flag string if a SQL-injection pattern is found, else ``None``."""
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(text):
            return "sql_injection_attempt"
    return None


def _detect_html_tags(text: str) -> str | None:
    """Return a flag string if a dangerous HTML tag is found, else ``None``."""
    for pattern in _HTML_TAG_PATTERNS:
        if pattern.search(text):
            return "dangerous_html_tag"
    return None


def _detect_javascript(text: str) -> str | None:
    """Return a flag string if a suspicious JavaScript pattern is found, else ``None``."""
    for pattern in _JS_PATTERNS:
        if pattern.search(text):
            return "suspicious_javascript"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def validate(
    query: str | bytes,
    *,
    min_length: int = MIN_QUERY_LENGTH,
    max_length: int = MAX_QUERY_LENGTH,
) -> ValidationResult:
    """
    Validate and normalise a raw user query.

    The function is **stateless** and **fail-safe**: it never raises an
    exception.  Hard failures (empty input, out-of-range length) set
    ``is_valid`` to ``False`` and populate ``validation_errors``.
    Suspicious patterns (injection attempts, HTML, JS, spam) set
    ``is_valid`` to ``True`` but add entries to ``warning_flags``.

    Args:
        query:      Raw user input (``str`` or UTF-8 ``bytes``).
        min_length: Minimum acceptable character count (default 2).
        max_length: Maximum acceptable character count (default 5 000).

    Returns:
        ValidationResult with ``original_query``, ``cleaned_query``,
        ``is_valid``, ``validation_errors``, and ``warning_flags``.
    """
    try:
        return _validate_inner(query, min_length, max_length)
    except Exception as exc:
        logger.error("Unexpected validation failure: %s", exc, exc_info=True)
        raw = query if isinstance(query, str) else ""
        return ValidationResult(
            original_query=raw,
            cleaned_query="",
            is_valid=False,
            validation_errors=[f"Internal validation error: {exc}"],
            warning_flags=[],
        )


def _validate_inner(
    query: str | bytes,
    min_length: int,
    max_length: int,
) -> ValidationResult:
    # ── Step 0: encoding ──────────────────────────────────────────────────────
    original = _ensure_valid_utf8(query)

    if not original and isinstance(query, (bytes, bytearray)):
        return ValidationResult(
            original_query="",
            cleaned_query="",
            is_valid=False,
            validation_errors=["Input could not be decoded as valid UTF-8."],
            warning_flags=[],
        )

    errors: list[str] = []
    warnings: list[str] = []
    changes: list[str] = []

    # ── Step 1: trim ──────────────────────────────────────────────────────────
    cleaned = original.strip()
    trimmed_len = len(original) - len(cleaned)
    if trimmed_len > 0:
        changes.append(f"trimmed {trimmed_len} whitespace character(s)")

    # ── Step 2: empty / whitespace-only ───────────────────────────────────────
    if not cleaned:
        return ValidationResult(
            original_query=original,
            cleaned_query="",
            is_valid=False,
            validation_errors=["Query is empty or contains only whitespace."],
            warning_flags=[],
        )

    # ── Step 3: remove dangerous HTML tags ────────────────────────────────────
    before_html = len(cleaned)
    cleaned = _remove_html_tags(cleaned)
    after_html = len(cleaned)
    if after_html < before_html:
        changes.append(
            f"removed {before_html - after_html} character(s) of dangerous HTML"
        )

    # ── Step 4: remove special-character spam ─────────────────────────────────
    before_special = len(cleaned)
    cleaned = _remove_special_char_spam(cleaned)
    after_special = len(cleaned)
    if after_special < before_special:
        changes.append(
            f"removed {before_special - after_special} special-char spam character(s)"
        )

    # ── Step 5: normalise whitespace (clean up after removals) ────────────────
    cleaned = _normalize_whitespace(cleaned)

    # ── Step 6: strip control characters ──────────────────────────────────────
    before_ctrl = len(cleaned)
    cleaned = _strip_control_characters(cleaned)
    after_ctrl = len(cleaned)
    if after_ctrl < before_ctrl:
        changes.append(
            f"removed {before_ctrl - after_ctrl} control character(s)"
        )

    # ── Step 7: Unicode NFKC ──────────────────────────────────────────────────
    before_uni = len(cleaned)
    cleaned = _normalize_unicode(cleaned)
    after_uni = len(cleaned)
    if after_uni != before_uni:
        changes.append(f"unicode normalised (length {before_uni} → {after_uni})")

    # ── Step 8: maximum length (BEFORE spam normalization) ────────────────────
    if len(cleaned) > max_length:
        errors.append(
            f"Query exceeds the maximum length of {max_length} "
            f"character(s) (got {len(cleaned)})."
        )

    # ── Step 9: normalise spam ────────────────────────────────────────────────
    before_repeat = len(cleaned)
    cleaned = _normalize_repeated_characters(cleaned)
    cleaned = _normalize_repeated_punctuation(cleaned)
    after_repeat = len(cleaned)
    if after_repeat < before_repeat:
        changes.append(
            f"collapsed {before_repeat - after_repeat} repeated character(s)"
        )

    # ── Step 10: minimum length (AFTER spam normalization) ────────────────────
    if len(cleaned) < min_length:
        errors.append(
            f"Query is shorter than the minimum length of {min_length} "
            f"character(s) after cleaning (got {len(cleaned)})."
        )

    # ── Step 11: security / injection warnings (non-blocking) ─────────────────
    flag = _detect_prompt_injection(cleaned)
    if flag:
        warnings.append(flag)

    flag = _detect_sql_injection(cleaned)
    if flag:
        warnings.append(flag)

    flag = _detect_html_tags(cleaned)
    if flag:
        warnings.append(flag)

    flag = _detect_javascript(cleaned)
    if flag:
        warnings.append(flag)

    if warnings:
        logger.warning(
            "Suspicious patterns detected in query [%s…]: %s",
            cleaned[:60],
            ", ".join(warnings),
        )

    # ── Detailed change logging ───────────────────────────────────────────────
    is_valid = len(errors) == 0

    if is_valid:
        if changes:
            logger.info(
                "Validation passed for query [%s…] (len=%d, changes=%s, warnings=%d)",
                cleaned[:60],
                len(cleaned),
                "; ".join(changes),
                len(warnings),
            )
        else:
            logger.info(
                "Validation passed for query [%s…] (len=%d, no changes needed, warnings=%d)",
                cleaned[:60],
                len(cleaned),
                len(warnings),
            )
    else:
        logger.warning(
            "Validation failed for query [%s…]: %s",
            original[:60],
            "; ".join(errors),
        )

    return ValidationResult(
        original_query=original,
        cleaned_query=cleaned,
        is_valid=is_valid,
        validation_errors=errors,
        warning_flags=warnings,
    )
