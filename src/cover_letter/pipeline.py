"""
pipeline.py — Step 4: Chains JD Parser → Smart Retriever → Content Generator.

Single entry point: call generate_cover_letter_content(jd_text) and get
back everything — the parsed JD, the chunks used, and the generated content.
"""

import logging
from .jd_parser        import JDParser
from .smart_retriever  import retrieve_smart
from .content_generator import generate_content
from .models            import JDParsedResult

logger = logging.getLogger("cover_letter.pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [CL:Pipeline] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# Output model — what the pipeline returns
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field

class CoverLetterResult(BaseModel):
    """
    The full output of the pipeline.
    """
    parsed_jd       : JDParsedResult      # The structured JD from Step 1
    chunks_used     : list[dict]          # The retrieved chunks from Step 2
    generated_content: str               # The raw cover letter text from Step 3
    num_chunks_used : int = 0            # How many chunks were used as evidence


# ─────────────────────────────────────────────────────────────────────────────
# The singleton parser — created once, reused for every request
# ─────────────────────────────────────────────────────────────────────────────

_parser = JDParser()


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline function — this is the ONLY thing the API router calls
# ─────────────────────────────────────────────────────────────────────────────

def generate_cover_letter_content(jd_text: str) -> CoverLetterResult:
    """
    Full pipeline: Raw JD text → Parsed JD → Retrieved Chunks → Generated Content.

    Args:
        jd_text: The raw job description text pasted by the user.

    Returns:
        CoverLetterResult with parsed_jd, chunks_used, and generated_content.
    """

    logger.info("Pipeline started.")

    # ── Step 1: Parse the JD ─────────────────────────────────────────────────
    logger.info("Step 1: Parsing JD...")
    parsed_jd = _parser.parse(jd_text)
    logger.info("Step 1 done — title='%s', domain='%s', skills=%d",
                parsed_jd.project_title, parsed_jd.industry_domain, len(parsed_jd.required_skills))

    # ── Step 2: Retrieve relevant chunks from Qdrant ─────────────────────────
    logger.info("Step 2: Retrieving relevant chunks...")
    chunks = retrieve_smart(parsed_jd)
    logger.info("Step 2 done — %d chunks retrieved.", len(chunks))

    # ── Step 3: Generate cover letter content ─────────────────────────────────
    logger.info("Step 3: Generating cover letter content...")
    content = generate_content(parsed_jd, chunks)
    logger.info("Step 3 done — %d characters generated.", len(content))

    logger.info("Pipeline completed successfully.")

    return CoverLetterResult(
        parsed_jd        = parsed_jd,
        chunks_used      = chunks,
        generated_content = content,
        num_chunks_used  = len(chunks),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Quick test — run directly: python -m src.cover_letter.pipeline
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    sample_jd = """
    We need an automation engineer to maintain and extend our n8n and Make.com pipelines.
    We use Zoho CRM and Zoho Books, and need help completing our bank reconciliation 
    automation and building out a new CRM for a second business unit.
    Experience with REST APIs, Brevo, and Apollo is a big plus.
    Full-time, 3-month contract, Dubai timezone overlap required.
    """

    result = generate_cover_letter_content(sample_jd)

    print("\n===== PIPELINE RESULT =====")
    print(f"Project Title   : {result.parsed_jd.project_title}")
    print(f"Chunks Used     : {result.num_chunks_used}")
    print(f"\n--- GENERATED CONTENT ---\n")
    print(result.generated_content)
