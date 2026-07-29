"""
proposal_writer.py — Generates a full structured proposal using Gemini.

Takes:
  - requirements dict (from chat_analyzer)
  - web_context string (from Tavily search)

Returns the complete proposal as a markdown string.
"""

import os
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger("proposal_generator.proposal_writer")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [ProposalWriter] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False

_GEMINI_MODEL = "gemini-3.1-flash-lite"

_PROMPT_TEMPLATE = """\
You are a senior proposal writer with 10+ years of experience winning enterprise software contracts.

Write a complete, professional project proposal based on the client requirements and web research below.

════════════════════════════════════════════════════════
CLIENT REQUIREMENTS (extracted from conversation):
════════════════════════════════════════════════════════
Project Title      : {project_title}
Industry/Domain    : {industry}
Client Requirements: {client_requirements}
Scope of Work      : {scope_of_work}
Tech Stack         : {tech_stack}
Timeline           : {timeline}
Budget             : {budget}
Pain Points        : {pain_points}

════════════════════════════════════════════════════════
WEB RESEARCH (current market data):
════════════════════════════════════════════════════════
{web_context}

════════════════════════════════════════════════════════
INSTRUCTIONS:
════════════════════════════════════════════════════════
Write a complete proposal with these EXACT sections in this order:

## Executive Summary
2-3 paragraphs. Hook the client. Show you understand their exact problem.
Reference their specific pain points and requirements directly.

## Understanding of Requirements
Demonstrate deep understanding of what they need.
Use bullet points showing you've read their brief carefully.

## Proposed Solution & Technical Approach
How you will solve their problem specifically.
Mention the technical architecture and key technologies involved.

## Project Scope & Deliverables
Clear list of what is included (and what is NOT included).
Specific, measurable deliverables.

## Project Timeline & Milestones
Phase-by-phase breakdown with realistic timeframes.
Key milestones and delivery checkpoints.

## Investment & Pricing
Pricing breakdown anchored to the budget (if mentioned).
If no budget mentioned, provide a realistic estimate range based on the scope.
What's included in the price.

## Why Choose Us
3-4 specific, compelling reasons.
Reference relevant experience or capabilities.

## Next Steps
Clear call to action.
What happens after they say yes.

Rules:
- Sound confident, specific, and professional — NOT generic.
- Every section must directly reference the client's specific project.
- Do NOT use filler phrases like "I hope this finds you well".
- Do NOT make up statistics or fabricate experience.
- Format with markdown headings (##, ###) and bullet points.
- Use web research data naturally where relevant (pricing benchmarks, tech facts).
"""


def _list_to_str(items) -> str:
    if not items:
        return "Not specified"
    if isinstance(items, list):
        return ", ".join(str(i) for i in items if i)
    return str(items) or "Not specified"


def write_proposal(requirements: dict, web_context: str = "") -> str:
    """
    Generate a full proposal document.

    Args:
        requirements: Dict from chat_analyzer.analyze_chat()
        web_context:  Formatted string of Tavily web search results

    Returns:
        The generated proposal as a markdown string.
    """
    prompt = _PROMPT_TEMPLATE.format(
        project_title       = requirements.get("project_title") or "Not specified",
        industry            = requirements.get("industry") or "Not specified",
        client_requirements = _list_to_str(requirements.get("client_requirements")),
        scope_of_work       = _list_to_str(requirements.get("scope_of_work")),
        tech_stack          = _list_to_str(requirements.get("tech_stack")),
        timeline            = requirements.get("timeline") or "Not specified",
        budget              = requirements.get("budget") or "Not specified",
        pain_points         = _list_to_str(requirements.get("pain_points")),
        web_context         = web_context or "No web research available.",
    )

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        logger.info(
            "Generating proposal for: '%s'",
            requirements.get("project_title", "Unknown")
        )

        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )

        content = response.text.strip()
        logger.info("Proposal generated (%d characters).", len(content))
        return content

    except Exception as exc:
        logger.error("Proposal generation failed: %s", exc)
        return "Error: Could not generate proposal. Please try again."
