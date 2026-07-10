import os
import sys
import logging

# Allow imports from project root (config.py lives there)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COLLECTION_NAME,
    MAX_CHUNK_SIZE,
    CHUNK_OVERLAP,
    BATCH_SIZE,
)

from extractor import extract_from_pdf
from categorizer import categorize_proposal
from chunker import chunk_document
from embedder import embed_chunks
from vector_store import upsert_vectors

logger = logging.getLogger("pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[Pipeline] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False


def process_pdf(pdf_path: str, collection_name: str = COLLECTION_NAME) -> dict:
    """
    Run the full pipeline for a single PDF file:
        Extract → Categorize → Chunk → Embed → Store in Qdrant

    Args:
        pdf_path:        Absolute or relative path to the PDF file.
        collection_name: Qdrant collection to store vectors in.

    Returns:
        A summary dict with keys:
            document, chunks, embeddings, stored, category, collection, success
    """
    summary = {
        "document": os.path.basename(pdf_path),
        "chunks": 0,
        "embeddings": 0,
        "stored": 0,
        "category": "",
        "collection": collection_name,
        "success": False,
    }

    # ── Step 0: Validate PDF path ─────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f" Processing: {os.path.basename(pdf_path)}")
    print(f"{'='*50}")

    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

    # ── Step 1: Extract text ──────────────────────────────────────────────────
    print("[1/5] Extracting text from PDF...")
    try:
        text = extract_from_pdf(pdf_path)
        if not text or not text.strip():
            raise ValueError("Extracted text is empty.")
        logger.info(f"Extracted {len(text)} characters.")
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise RuntimeError(f"Failed to extract text from '{pdf_path}': {e}") from e

    # ── Step 2: Categorize ────────────────────────────────────────────────────
    print("[2/5] Categorizing document...")
    pdf_name = os.path.basename(pdf_path)
    try:
        category = categorize_proposal(pdf_name, text)
        summary["category"] = category
        logger.info(f"Category: {category}")
    except Exception as e:
        logger.warning(f"Categorization failed: {e}. Defaulting to 'Uncategorized'.")
        category = "Uncategorized"
        summary["category"] = category

    # ── Step 3: Chunk ─────────────────────────────────────────────────────────
    print("[3/5] Chunking document...")
    try:
        metadata = {
            "file_name": pdf_name,
            "category": category,
        }
        chunks = chunk_document(
            text,
            max_chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            metadata=metadata,
        )
        if not chunks:
            raise ValueError("No chunks produced.")
        summary["chunks"] = len(chunks)
        logger.info(f"Produced {len(chunks)} chunks.")
    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        raise RuntimeError(f"Failed to chunk document '{pdf_name}': {e}") from e

    # ── Step 4: Embed ─────────────────────────────────────────────────────────
    print(f"[4/5] Generating embeddings for {len(chunks)} chunk(s)...")
    try:
        embedded = embed_chunks(chunks, document_name=pdf_name, category=category)
        if not embedded:
            raise ValueError("No embeddings produced.")
        summary["embeddings"] = len(embedded)
        logger.info(f"Generated {len(embedded)} embeddings.")
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise RuntimeError(f"Failed to generate embeddings for '{pdf_name}': {e}") from e

    # ── Step 5: Store in Qdrant ───────────────────────────────────────────────
    print(f"[5/5] Storing {len(embedded)} vector(s) in Qdrant collection '{collection_name}'...")
    try:
        stored = upsert_vectors(
            embedded,
            collection_name=collection_name,
            batch_size=BATCH_SIZE,
        )
        summary["stored"] = stored
        logger.info(f"Stored {stored} vectors in '{collection_name}'.")
    except ConnectionError as e:
        logger.error(f"Qdrant connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Vector storage failed: {e}")
        raise RuntimeError(f"Failed to store vectors for '{pdf_name}': {e}") from e

    summary["success"] = True

    # ── Print summary ─────────────────────────────────────────────────────────
    _print_summary(summary)
    return summary


def _print_summary(summary: dict):
    """Print a formatted pipeline summary to stdout."""
    print(f"\n{'-'*40}")
    print(" Document Processed Successfully")
    print(f"{'-'*40}")
    print(f"  Document  : {summary['document']}")
    print(f"  Chunks    : {summary['chunks']}")
    print(f"  Embeddings: {summary['embeddings']}")
    print(f"  Stored in Qdrant: {summary['stored']}")
    print(f"  Category  : {summary['category']}")
    print(f"  Collection: {summary['collection']}")
    print(f"{'-'*40}\n")


if __name__ == "__main__":
    # Quick test: process one hardcoded PDF
    test_pdf = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "raw_pdfs", "POC_Proposal.pdf"
    )
    process_pdf(test_pdf)
