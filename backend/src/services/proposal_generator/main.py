"""
main.py — End-to-End Proposal Generation Execution Script.

Demonstrates building a complete proposal matching AB Ark's reference PDF layout:
- Page 1 Cover (Lumova AI)
- Pages 2+ Body sections (Executive summary, POC assessment, Phase 1 & 2 banners, tech stack table, milestones table, next steps table)
- Page X of Y footers & 3-column headers with dynamic date & proposal ID

Run command:
    python -m src.services.proposal_generator.main
"""

import os
from .proposal_writer import generate_full_markdown_proposal
from .docx_generator import build_proposal_docx_from_markdown
from .utils import generate_proposal_id, get_formatted_current_date, get_default_version


def run_demo():
    requirements = {
        "project_title": "Lumova AI",
        "client_name": "Yancy",
        "industry": "Real Estate AI & Computer Vision",
        "scope_of_work": [
            "3D Digital Twin building health score engine",
            "YOLOv26 defect detection model on AWS SageMaker",
            "Drone imagery ingestion pipeline on AWS S3 & Lambda",
            "Stripe billing and multi-tenant FastAPI backend"
        ],
        "tech_stack": ["React 19", "Python FastAPI", "AWS SageMaker", "PostgreSQL RDS", "OpenCV"],
        "timeline": "Phase 1: 5 weeks, Phase 2: 9 weeks",
        "budget": "$28,000"
    }

    doc_id = generate_proposal_id()
    date_str = get_formatted_current_date()
    version = get_default_version()

    print(f"=== Starting AB Ark End-to-End Proposal Generation ===")
    print(f"Project Title : {requirements['project_title']}")
    print(f"Client Name   : {requirements['client_name']}")
    print(f"Proposal ID   : {doc_id}")
    print(f"Dated         : {date_str}")
    print(f"Version       : {version}\n")

    # Step 1: Generate Multi-Section Markdown Content
    print("[1/2] Generating multi-section Markdown proposal via Gemini LLM loop...")
    markdown_content = generate_full_markdown_proposal(requirements)

    # Step 2: Assemble Page 1 Cover + Pages 2+ Body into DOCX
    print("\n[2/2] Assembling Page 1 Cover + Pages 2+ Body into AB Ark DOCX document...")
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "output"
    )
    output_docx = os.path.join(output_dir, "final_ab_ark_proposal.docx")

    build_proposal_docx_from_markdown(
        markdown_content=markdown_content,
        project_title=requirements["project_title"],
        client_name=requirements["client_name"],
        proposal_id=doc_id,
        date_str=date_str,
        version=version,
        output_path=output_docx
    )

    print(f"=======================================================")
    print(f"SUCCESS! Final proposal document generated successfully:")
    print(f"File: {output_docx}")
    print(f"=======================================================")



if __name__ == "__main__":
    run_demo()
