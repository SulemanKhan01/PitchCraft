"""
chat_analyzer.py — Extracts structured client requirements from a conversation.

Takes the full list of chat messages and uses Gemini to identify:
  - project_title
  - client_requirements
  - tech_stack
  - timeline
  - budget
  - pain_points
  - industry
  - scope_of_work
"""

import os
import logging
from dotenv import load_dotenv
from google import genai
import json
import re

load_dotenv()

logger = logging.getLogger("proposal_generator.chat_analyzer")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [ChatAnalyzer] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

from src.config import GEMINI_MODEL

_GEMINI_MODEL = GEMINI_MODEL

_PROMPT = """\
You are an expert business analyst. Read the conversation below between a user \
and an AI assistant. Extract the client's project requirements.

Return ONLY a valid JSON object with these exact fields \
(use empty string "" or empty list [] if information is missing):
{{
  "project_title": "Short descriptive title of the project",
  "client_requirements": ["requirement 1", "requirement 2"],
  "tech_stack": ["technology 1", "technology 2"],
  "timeline": "e.g. 3 months, ASAP, by Q4 2025, or empty string",
  "budget": "e.g. $5000, $10k/month, open to discussion, or empty string",
  "pain_points": ["problem 1", "problem 2"],
  "industry": "e.g. healthcare, fintech, e-commerce, or empty string",
  "scope_of_work": ["task 1", "task 2"]
}}

Rules:
1. Extract ONLY what is explicitly stated or strongly implied.
2. Do NOT invent or guess any details.
3. If the conversation does not mention a field, use "" or [].

Conversation:
\"\"\"
{conversation}
\"\"\"

JSON Response:"""


def _parse_json(raw: str) -> dict | None:
    """Extract and parse JSON from LLM response (handles markdown fences)."""
    if not raw:
        return None
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\})", cleaned)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return None


def _format_conversation(messages: list[dict]) -> str:
    """Convert message list into readable conversation string."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines)


def _empty_requirements() -> dict:
    return {
        "project_title": "",
        "client_requirements": [],
        "tech_stack": [],
        "timeline": "",
        "budget": "",
        "pain_points": [],
        "industry": "",
        "scope_of_work": [],
    }


def analyze_chat(messages: list[dict]) -> dict:
    """
    Analyze a full conversation and extract structured client requirements.

    Args:
        messages: List of dicts with 'role' and 'content' keys.

    Returns:
        Dict with extracted fields.
    """
    if not messages:
        logger.warning("analyze_chat called with empty messages.")
        return _empty_requirements()

    conversation_text = _format_conversation(messages)
    prompt = _PROMPT.format(conversation=conversation_text)

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        logger.info("Analyzing %d messages with Gemini...", len(messages))
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )

        data = _parse_json(response.text)

        if data and isinstance(data, dict):
            logger.info(
                "Chat analysis done. Project: '%s'",
                data.get("project_title", "N/A")
            )
            return data

        logger.warning("Could not parse JSON from Gemini response.")

    except Exception as exc:
        logger.error("Chat analysis failed: %s", exc)

    return _empty_requirements()
