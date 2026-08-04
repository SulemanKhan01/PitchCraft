"""
docx_generator.py — AB Ark Master Proposal Document Assembly Engine.

Renders Page 1 Cover via docxtpl, parses full Markdown body via markdown_parser onto python-docx pages (starting Page 2),
and merges into the final output document via docxcompose.
"""

import os
import io
import logging
from docxtpl import DocxTemplate, InlineImage
from docx import Document
from docxcompose.composer import Composer

from .constants import (
    HEADER_LOGO_WIDTH, COVER_CENTER_LOGO_WIDTH,
    MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT
)
from .utils import generate_proposal_id, get_formatted_current_date, get_default_version
from .styles import register_proposal_styles
from .header_footer import setup_header_and_footer
from .markdown_parser import parse_markdown_to_docx

logger = logging.getLogger("proposal_generator.docx_generator")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [DOCX:Gen] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def build_proposal_docx_from_markdown(
    markdown_content: str,
    project_title: str = "Software Platform",
    client_name: str = "Valued Client",
    proposal_subtitle: str = "Proposal for Building Production Platform",
    proposal_id: str = None,
    date_str: str = None,
    version: str = None,
    output_path: str = None,
    logo_path: str = None
) -> bytes:
    """
    Master Assembly Engine:
    1. Renders Page 1 Cover via docxtpl.
    2. Constructs Pages 2+ Body via python-docx + markdown_parser.
    3. Merges Cover + Body via docxcompose into final DOCX byte stream.
    """
    # Auto-generate dynamic metadata if not provided
    if not proposal_id:
        proposal_id = generate_proposal_id()
    if not date_str:
        date_str = get_formatted_current_date()
    if not version:
        version = get_default_version()

    if not logo_path:
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "data", "templates", "image.png"
        )

    cover_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "data", "templates", "cover_template.docx"
    )

    # Ensure cover_template.docx exists
    if not os.path.exists(cover_template_path):
        from .create_cover_template import build_cover_template
        build_cover_template(cover_template_path)

    # ================= 1. RENDER PAGE 1 COVER (docxtpl) ================= #
    logger.info(f"Rendering Page 1 Cover for '{project_title}' (ID: {proposal_id}, Date: {date_str})...")
    cover_doc = DocxTemplate(cover_template_path)

    context = {
        "client_project_name": project_title,
        "proposal_subtitle": proposal_subtitle,
        "client_name": client_name,
        "proposal_id": proposal_id,
        "date": date_str,
        "version": version
    }

    if os.path.exists(logo_path):
        context["header_logo"] = InlineImage(cover_doc, logo_path, width=HEADER_LOGO_WIDTH)
        context["center_logo"] = InlineImage(cover_doc, logo_path, width=COVER_CENTER_LOGO_WIDTH)
    else:
        context["header_logo"] = ""
        context["center_logo"] = ""

    cover_doc.render(context)

    # Save rendered cover page to in-memory buffer
    cover_buffer = io.BytesIO()
    cover_doc.save(cover_buffer)
    cover_buffer.seek(0)

    # ================= 2. BUILD PAGES 2+ BODY DOCUMENT (python-docx) ================= #
    logger.info("Constructing Pages 2+ Body Document via python-docx & markdown_parser...")
    body_doc = Document()

    # Configure Margins (0.8")
    sec = body_doc.sections[0]
    sec.top_margin = MARGIN_TOP
    sec.bottom_margin = MARGIN_BOTTOM
    sec.left_margin = MARGIN_LEFT
    sec.right_margin = MARGIN_RIGHT

    # Register AB Ark typography & table styles
    register_proposal_styles(body_doc)

    # Setup Running Headers & Footers (Page X of Y, links) for Body Pages
    setup_header_and_footer(
        sec,
        logo_path=logo_path,
        doc_id=proposal_id,
        version=version
    )

    # Parse & Render full Markdown proposal content starting on Page 2
    parse_markdown_to_docx(body_doc, markdown_content)

    # ================= 3. MERGE COVER PAGE & BODY PAGES (docxcompose) ================= #
    logger.info("Merging Page 1 Cover + Pages 2+ Body via docxcompose...")
    final_cover_doc = Document(cover_buffer)
    composer = Composer(final_cover_doc)
    composer.append(body_doc)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        composer.save(output_path)
        logger.info(f"Successfully saved final proposal to: '{output_path}'")

    final_buffer = io.BytesIO()
    composer.save(final_buffer)
    return final_buffer.getvalue()


# Verification runner when executed directly
if __name__ == "__main__":
    test_md = """
## 1. Executive Summary

This proposal outlines the production roadmap for Lumova AI.

### 1.1 Objectives

- High performance backend
- Multi-tenant isolation

## 3. Phase 1 — MVP Production Build

| Milestone | Deliverable | Amount |
| --- | --- | --- |
| M1 | AWS Setup | $1,500 |
| M2 | FastAPI Backend | $2,200 |
"""
    output_test_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "output", "test_proposal_part7.docx"
    )
    build_proposal_docx_from_markdown(
        markdown_content=test_md,
        project_title="Lumova AI Test",
        client_name="Yancy",
        output_path=output_test_path
    )
    print("--- docx_generator.py Part 7 verification completed successfully ---")
