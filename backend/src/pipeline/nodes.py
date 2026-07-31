"""
nodes.py — 5 Node execution steps for PDF processing pipeline.
"""

import os
import logging
from typing import Dict, Any
from config import MAX_CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE
from src.extraction.extractor import extract_from_pdf
from src.services.categorizer import categorize_proposal
from src.chunking.chunker import chunk_document
from src.embeddings.embedder import embed_chunks
from src.retrieval.vector_store import upsert_vectors
from .state import PDFProcessingState

logger = logging.getLogger("pipeline.nodes")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [PDF:Nodes] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def extract_text_node(state: PDFProcessingState) -> Dict[str, Any]:
    """Node 1/5: Extract text from PDF."""
    pdf_path = state["pdf_path"]
    logger.info(f"[Node 1/5: extract_text] Extracting text from '{os.path.basename(pdf_path)}'...")
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

        text = extract_from_pdf(pdf_path)
        if not text or not text.strip():
            raise ValueError("Extracted text is empty.")

        logger.info(f"[Node 1/5: extract_text] Successfully extracted {len(text)} characters.")
        return {"extracted_text": text}
    except Exception as exc:
        logger.error(f"[Node 1/5: extract_text] Text extraction failed: {exc}")
        return {"extracted_text": "", "error": f"Extraction failed: {str(exc)}"}


def categorize_node(state: PDFProcessingState) -> Dict[str, Any]:
    """Node 2/5: Categorize document."""
    if state.get("error"):
        logger.warning("[Node 2/5: categorize] Skipping due to prior error.")
        return {"category": "Uncategorized"}

    logger.info("[Node 2/5: categorize] Categorizing document...")
    try:
        pdf_name = os.path.basename(state["pdf_path"])
        category = categorize_proposal(pdf_name, state["extracted_text"])
        logger.info(f"[Node 2/5: categorize] Category assigned: '{category}'")
        return {"category": category}
    except Exception as exc:
        logger.warning(f"[Node 2/5: categorize] Failed: {exc}. Defaulting to 'Uncategorized'.")
        return {"category": "Uncategorized"}


def chunk_node(state: PDFProcessingState) -> Dict[str, Any]:
    """Node 3/5: Chunk document text into smaller passages."""
    if state.get("error") or not state.get("extracted_text"):
        logger.warning("[Node 3/5: chunk] Skipping due to missing text or prior error.")
        return {"chunks": []}

    logger.info("[Node 3/5: chunk] Chunking document...")
    try:
        pdf_name = os.path.basename(state["pdf_path"])
        metadata = {"file_name": pdf_name, "category": state.get("category", "Uncategorized")}
        chunks = chunk_document(
            state["extracted_text"],
            max_chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            metadata=metadata,
        )
        logger.info(f"[Node 3/5: chunk] Produced {len(chunks)} text chunks.")
        return {"chunks": chunks}
    except Exception as exc:
        logger.error(f"[Node 3/5: chunk] Chunking failed: {exc}")
        return {"chunks": [], "error": f"Chunking failed: {str(exc)}"}


def embed_node(state: PDFProcessingState) -> Dict[str, Any]:
    """Node 4/5: Generate vector embeddings for text chunks."""
    if state.get("error") or not state.get("chunks"):
        logger.warning("[Node 4/5: embed] Skipping due to missing chunks or prior error.")
        return {"embeddings": []}

    logger.info(f"[Node 4/5: embed] Generating embeddings for {len(state['chunks'])} chunks...")
    try:
        pdf_name = os.path.basename(state["pdf_path"])
        embedded = embed_chunks(state["chunks"], document_name=pdf_name, category=state.get("category", ""))
        logger.info(f"[Node 4/5: embed] Generated {len(embedded)} vector embeddings.")
        return {"embeddings": embedded}
    except Exception as exc:
        logger.error(f"[Node 4/5: embed] Embedding failed: {exc}")
        return {"embeddings": [], "error": f"Embedding failed: {str(exc)}"}


def store_vectors_node(state: PDFProcessingState) -> Dict[str, Any]:
    """Node 5/5: Upsert vectors into Qdrant collection."""
    if state.get("error") or not state.get("embeddings"):
        logger.warning("[Node 5/5: store] Skipping due to missing embeddings or prior error.")
        return {"stored": 0, "success": False}

    logger.info(f"[Node 5/5: store] Upserting {len(state['embeddings'])} vectors into Qdrant '{state['collection_name']}'...")
    try:
        stored = upsert_vectors(state["embeddings"], collection_name=state["collection_name"], batch_size=BATCH_SIZE)
        logger.info(f"[Node 5/5: store] Successfully stored {stored} vectors in '{state['collection_name']}'.")
        return {"stored": stored, "success": True}
    except Exception as exc:
        logger.error(f"[Node 5/5: store] Qdrant storage failed: {exc}")
        return {"stored": 0, "success": False, "error": f"Vector storage failed: {str(exc)}"}
