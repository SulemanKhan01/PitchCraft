

import logging
from typing import Dict, Any
from .state import CoverLetterState
from .jd_parser import JDParser
from .smart_retriever import retrieve_smart
from .content_generator import generate_content

logger = logging.getLogger("cover_letter.nodes")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [CL:Nodes] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False

_parser = JDParser()


def parse_jd_node(state: CoverLetterState) -> Dict[str, Any]:
    """Node 1: Parses job description into structured criteria."""
    logger.info("[Node 1/3: parse_jd] Parsing job description...")
    try:
        parsed = _parser.parse(state["jd_text"])
        logger.info(f"[Node 1/3: parse_jd] Done — project='{parsed.project_title}', skills={len(parsed.required_skills)}")
        return {"parsed_jd": parsed}
    except Exception as exc:
        logger.error(f"[Node 1/3: parse_jd] Failed: {exc}")
        return {"error": f"JD parsing failed: {str(exc)}"}


def retrieve_chunks_node(state: CoverLetterState) -> Dict[str, Any]:
    """Node 2: Retrieves relevant evidence chunks from Qdrant."""
    if state.get("error"):
        logger.warning("[Node 2/3: retrieve_chunks] Skipping due to prior error.")
        return {}

    logger.info("[Node 2/3: retrieve_chunks] Querying vector DB...")
    try:
        chunks = retrieve_smart(state["parsed_jd"])
        logger.info(f"[Node 2/3: retrieve_chunks] Done — {len(chunks)} chunks retrieved.")
        return {"chunks": chunks}
    except Exception as exc:
        logger.error(f"[Node 2/3: retrieve_chunks] Retrieval failed: {exc}")
        return {"chunks": [], "error": f"Retrieval failed: {str(exc)}"}


def generate_content_node(state: CoverLetterState) -> Dict[str, Any]:
    """Node 3: Generates final cover letter text using Gemini."""
    if state.get("error") and not state.get("parsed_jd"):
        logger.error("[Node 3/3: generate_content] Cannot proceed without parsed JD.")
        return {"generated_content": "Cover letter generation failed."}

    logger.info("[Node 3/3: generate_content] Generating cover letter text...")
    try:
        content = generate_content(state["parsed_jd"], state.get("chunks") or [])
        logger.info(f"[Node 3/3: generate_content] Done — {len(content)} characters generated.")
        return {"generated_content": content}
    except Exception as exc:
        logger.error(f"[Node 3/3: generate_content] Generation failed: {exc}")
        return {"generated_content": "", "error": f"Generation failed: {str(exc)}"}
