"""
pipeline.py — LangGraph Entrypoint Wrapper for Cover Letter Generation.
"""

import logging
from pydantic import BaseModel
from .state import CoverLetterState
from .graph import cover_letter_graph
from .models import JDParsedResult

logger = logging.getLogger("cover_letter.pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [CL:Pipeline] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


class CoverLetterResult(BaseModel):
    """
    The full output model expected by FastAPI router.
    """
    parsed_jd: JDParsedResult
    chunks_used: list[dict]
    generated_content: str
    num_chunks_used: int = 0


def generate_cover_letter_content(jd_text: str) -> CoverLetterResult:
    """
    Main pipeline entrypoint called by FastAPI endpoint.
    Orchestrates execution via LangGraph.
    """
    logger.info("=== LangGraph Cover Letter Pipeline Started ===")

    initial_state: CoverLetterState = {
        "jd_text": jd_text,
        "parsed_jd": None,
        "chunks": None,
        "generated_content": None,
        "error": None,
    }

    # Execute compiled LangGraph graph
    final_state = cover_letter_graph.invoke(initial_state)

    logger.info("=== LangGraph Cover Letter Pipeline Completed ===")

    chunks = final_state.get("chunks") or []
    return CoverLetterResult(
        parsed_jd=final_state["parsed_jd"],
        chunks_used=chunks,
        generated_content=final_state.get("generated_content", ""),
        num_chunks_used=len(chunks),
    )


if __name__ == "__main__":
    sample_jd = """
    We need a Python software engineer with experience in FastAPI and Qdrant.
    Building automated AI workflows and REST APIs.
    """
    result = generate_cover_letter_content(sample_jd)
    print("\n===== PIPELINE RESULT =====")
    print(f"Chunks Used : {result.num_chunks_used}")
    print(f"Content     : {result.generated_content}")
