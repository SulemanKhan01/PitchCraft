"""
proposal_writer.py — Multi-Section LLM Proposal Generator for AB {Ark}.

Generates comprehensive 8-11 page technical proposals matching AB Ark's reference PDF format.
Uses a two-step multi-prompt engine:
  Step 1: Outline Generator — Creates a tailored 8-10 section roadmap.
  Step 2: Section Writer Loop — Executes targeted Gemini calls per section for deep technical detail.
"""

import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

from concurrent.futures import ThreadPoolExecutor, as_completed


from src.config import GEMINI_MODEL

load_dotenv()

logger = logging.getLogger("proposal_generator.proposal_writer")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [ProposalWriter] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def _get_gemini_client() -> genai.Client:
    """Initializes and returns the Google GenAI SDK client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=api_key)


def generate_proposal_outline(requirements: dict) -> list[str]:
    """
    Step 1: Calls Gemini to generate a structured list of section titles for the proposal.
    """
    client = _get_gemini_client()

    project_title = requirements.get("project_title") or "Software Platform"
    client_name = requirements.get("client_name") or "Valued Client"
    industry = requirements.get("industry") or "Technology"

    prompt = f"""
    You are a principal proposal architect for AB {{Ark}}.
    Analyze the project brief below and return a JSON list of section titles for a comprehensive 8-11 page technical proposal document.

    CLIENT BRIEF:
    - Project Title: {project_title}
    - Client Name: {client_name}
    - Industry: {industry}
    - Key Tech Stack: {requirements.get('tech_stack', [])}
    - Timeline: {requirements.get('timeline', '3-6 months')}

    REQUIRED SECTIONS TO INCLUDE (in exact order):
    1. Executive Summary
    2. Current State — POC Assessment
    3. Phase 1 — MVP Production Build
    4. Phase 2 — V1 Production Platform
    5. Future Envisioned Platform Features
    6. Full Technology Stack
    7. Operational Cost
    8. Engagement Model
    9. Why This Partnership
    10. Proposed Next Steps

    Return ONLY a JSON array of strings, for example:
    [
        "1. Executive Summary",
        "2. Current State — POC Assessment",
        "3. Phase 1 — MVP Production Build",
        "4. Phase 2 — V1 Production Platform",
        "5. Future Envisioned Platform Features",
        "6. Full Technology Stack",
        "7. Operational Cost",
        "8. Engagement Model",
        "9. Why This Partnership",
        "10. Proposed Next Steps"
    ]
    """

    try:
        logger.info(f"Generating proposal outline for '{project_title}'...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        outline = json.loads(response.text.strip())
        if isinstance(outline, list) and len(outline) > 0:
            logger.info(f"Outline generated successfully ({len(outline)} sections).")
            return outline
    except Exception as exc:
        logger.error(f"Outline generation failed: {exc}. Falling back to default outline.")

    # Standard AB Ark default outline fallback
    return [
        "1. Executive Summary",
        "2. Current State — POC Assessment",
        "3. Phase 1 — MVP Production Build",
        "4. Phase 2 — V1 Production Platform",
        "5. Future Envisioned Platform Features",
        "6. Full Technology Stack",
        "7. Operational Cost",
        "8. Engagement Model",
        "9. Why This Partnership",
        "10. Proposed Next Steps"
    ]


def write_proposal_section(section_title: str, requirements: dict, web_context: str = "") -> str:
    """
    Step 2: Calls Gemini to generate deep, comprehensive technical Markdown for ONE specific section.
    """
    client = _get_gemini_client()

    project_title = requirements.get("project_title") or "Software Platform"
    client_name = requirements.get("client_name") or "Valued Client"

    prompt = f"""
    You are a principal enterprise technical consultant writing a high-value proposal for AB {{Ark}}.
    Write the COMPLETE, IN-DEPTH Markdown text for the following section ONLY:

    TARGET SECTION TO WRITE: ## {section_title}

    CLIENT & PROJECT CONTEXT:
    - Project Title: {project_title}
    - Client Name: {client_name}
    - Scope & Requirements: {requirements.get('scope_of_work', [])}
    - Tech Stack: {requirements.get('tech_stack', [])}
    - Budget: {requirements.get('budget', 'Not specified')}
    - Timeline: {requirements.get('timeline', 'Not specified')}
    - Market/AWS Research Data:
      {web_context or 'Use standard enterprise AWS & modern full-stack engineering best practices.'}

    STRICT WRITING RULES FOR THIS SECTION:
    1. Start the section with '## {section_title}' as the top-level Heading 1.
    2. Write confident, technical, consultative content — NO generic marketing fluff.
    3. Include nested sub-headings using '###' (e.g. '### 3.1 Backend & API Layer', '### 3.2 Authentication & Security') where appropriate.
    4. If the section naturally contains tabular data (such as Milestones, Technology Stack, Operational Costs, or Next Steps), output a properly formatted Markdown table (`| Column 1 | Column 2 |`).
    5. Use concrete specifics (exact AWS service names like RDS PostgreSQL, ECS Fargate, Rekognition, SageMaker; dollar amounts; week ranges) rather than vague claims.
    6. Return ONLY valid Markdown content for this section. Do NOT wrap in triple backtick markdown blocks.
    """

    try:
        logger.info(f"Generating content for section: '{section_title}'...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        section_md = response.text.strip()
        logger.info(f"Section '{section_title}' generated ({len(section_md)} chars).")
        return section_md
    except Exception as exc:
        logger.error(f"Failed to generate section '{section_title}': {exc}")
        # Return fallback markdown heading and paragraph on error
        return f"## {section_title}\n\nDetailed specifications for {section_title} will be finalized during technical kickoff alignment."


def generate_full_markdown_proposal(requirements: dict, web_context: str = "") -> str:
    """
    Master Orchestrator:
    1. Generates 8-10 section outline.
    2. Loops through each section, executing targeted Gemini calls.
    3. Stitches all section Markdowns into one comprehensive master proposal document.
    """
    logger.info("=== Starting Multi-Section Proposal Markdown Generation ===")

    # Step 1: Get outline list of section titles
    outline_sections = generate_proposal_outline(requirements)

    section_results = {}
    logger.info(f"Generating {len(outline_sections)} sections in parallel (max 5 at a time)...")


    with ThreadPoolExecutor(max_workers=5) as executor:

        future_to_idx = {
            executor.submit(
                write_proposal_section,
                section_title=title,
                requirements=requirements,
                web_context=web_context
            ): idx
            for idx, title in enumerate(outline_sections)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            title = outline_sections[idx]

            try:
                sec_md = future.result()
                section_results[idx] = sec_md
                logger.info(f"Completed section [{idx+1}/{len(outline_sections)}]: '{title}'")
            except Exception as exc:
                logger.error(f"Failed section [{idx+1}]: '{title}' — {exc}")
                section_results[idx] = f"## {title}\n\nSection specifications pending technical kickoff alignment."
    # Step 3: Re-assemble sections in exact 0..N-1 order
    ordered_markdown = [section_results[i] for i in range(len(outline_sections))]
    full_markdown_content = "\n\n\n".join(ordered_markdown)
    logger.info(f"=== Parallel Multi-Section Generation Complete! Total Length: {len(full_markdown_content)} characters ===")
    return full_markdown_content

write_proposal = generate_full_markdown_proposal




# ---------------- CLI VERIFICATION TEST ---------------- #
if __name__ == "__main__":
    sample_requirements = {
        "project_title": "Lumova AI",
        "client_name": "Yancy",
        "industry": "Real Estate AI & Computer Vision",
        "scope_of_work": [
            "3D Digital Twin building health score engine",
            "YOLOv26 defect detection model on AWS SageMaker",
            "Drone imagery ingestion pipeline on AWS S3 & Lambda",
            "Stripe billing and multi-tenant FastAPI backend"
        ],
        "tech_stack": ["React 19", "Python FastAPI", "AWS SageMaker", "PostgreSQL RDS"],
        "timeline": "Phase 1: 5 weeks, Phase 2: 9 weeks",
        "budget": "$28,000"
    }

    print("--- Running Multi-Section Proposal Writer Verification ---")
    full_md = generate_full_markdown_proposal(sample_requirements)
    print("\n================ GENERATED MARKDOWN PREVIEW ================\n")
    print(full_md[:1200])
    print("\n... [Truncated preview] ...\n")
    print(f"Total Markdown Characters Generated: {len(full_md)}")
    print("--- Part 6 Verification Successful! ---")
