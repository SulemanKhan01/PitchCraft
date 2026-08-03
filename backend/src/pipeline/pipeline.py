"""
pipeline.py — LangGraph Public Entrypoint for PDF Ingestion.
"""

import os
import logging
from config import COLLECTION_NAME
from .state import PDFProcessingState
from .graph import pdf_processing_graph

logger = logging.getLogger("pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [PDF:Pipeline] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def process_pdf(pdf_path: str, collection_name: str = COLLECTION_NAME) -> dict:
    """
    Public entrypoint called by FastAPI upload router (/api/proposals/upload).
    Orchestrates execution via LangGraph.
    """
    logger.info("=== LangGraph PDF Ingestion Pipeline Started ===")

    initial_state: PDFProcessingState = {
        "pdf_path": pdf_path,
        "collection_name": collection_name,
        "extracted_text": None,
        "category": "Uncategorized",
        "chunks": [],
        "embeddings": [],
        "stored": 0,
        "success": False,
        "error": None,
    }

    # Execute compiled LangGraph graph
    final_state = pdf_processing_graph.invoke(initial_state)

    logger.info("=== LangGraph PDF Ingestion Pipeline Completed ===")

    return {
        "document": os.path.basename(pdf_path),
        "chunks": len(final_state.get("chunks") or []),
        "embeddings": len(final_state.get("embeddings") or []),
        "stored": final_state.get("stored", 0),
        "category": final_state.get("category", "Uncategorized"),
        "collection": collection_name,
        "success": final_state.get("success", False),
    }


# Standalone CLI test
if __name__ == "__main__":
    test_pdf = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "raw_pdfs", "POC_Proposal.pdf"
    )
    if os.path.exists(test_pdf):
        res = process_pdf(test_pdf)
        print("\n===== INGESTION RESULT =====")
        print(res)
    else:
        print(f"Test file not found: {test_pdf}")
 