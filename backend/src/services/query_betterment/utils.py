"""
utils.py — Shared utilities for the Query Betterment Pipeline.

Responsibilities:
  - LLM client factory (singleton, injected into every stage)
  - Timer context manager (ms-precision)
  - Robust JSON extraction from LLM responses (handles markdown fences)
  - Model name constant
"""
from __future__ import annotations

import os
import re
import json
import time
from contextlib import contextmanager
from typing import Any, Generator

from dotenv import load_dotenv
from google import genai

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# LLM Model Constant
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_FLASH_LITE: str = "gemini-3.1-flash-lite"

# ─────────────────────────────────────────────────────────────────────────────
# Gemini Client — Singleton Factory
# ─────────────────────────────────────────────────────────────────────────────

_gemini_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    """
    Return the shared Gemini client instance (lazy, singleton).

    Raises:
        EnvironmentError: If GEMINI_API_KEY is not set.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# ─────────────────────────────────────────────────────────────────────────────
# Timer Context Manager
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def timer() -> Generator[dict[str, float], None, None]:
    """
    Context manager that measures wall-clock execution time in milliseconds.

    Usage:
        with timer() as t:
            do_work()
        print(t["elapsed_ms"])
    """
    record: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield record
    finally:
        record["elapsed_ms"] = (time.perf_counter() - start) * 1_000


# ─────────────────────────────────────────────────────────────────────────────
# JSON Extraction from LLM Responses
# ─────────────────────────────────────────────────────────────────────────────

def parse_json_from_llm(raw: str) -> Any:
    """
    Robustly extract and parse a JSON object or array from an LLM response.

    Handles:
      - Bare JSON
      - Markdown code fences (```json ... ``` or ``` ... ```)
      - Responses with leading/trailing prose

    Returns:
        Parsed Python object (dict, list, etc.) or None if parsing fails.
    """
    if not raw:
        return None

    # 1. Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    # 2. Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Extract first {...} or [...] block from the cleaned text
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None
