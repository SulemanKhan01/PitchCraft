import logging
import uuid
from typing import Optional

logger = logging.getLogger("embedder")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[Embedder] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

# Lazy-loaded singleton model
_model = None


def _get_model():
    """Load SentenceTransformer model once (singleton/lazy loading)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            import sys
            sys.path.insert(0, "..")
            from config import EMBEDDING_MODEL
            logger.info(f"Loading embedding model: '{EMBEDDING_MODEL}' ...")
            _model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Model '{EMBEDDING_MODEL}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Embedding model could not be loaded: {e}") from e
    return _model


def embed_chunks(chunks: list[dict], document_name: str = "", category: str = "") -> list[dict]:
    """
    Generate embeddings for every chunk.

    Args:
        chunks: List of chunk dicts from chunk_document(), each with 'text' and 'metadata'.
        document_name: The source document filename.
        category: The category assigned to this document.

    Returns:
        List of embedded chunk dicts with shape:
        {
            "id": str (uuid),
            "text": str,
            "embedding": list[float],
            "metadata": {
                "document_name": str,
                "category": str,
                "section": str,
                "chunk_index": int
            }
        }
    """
    if not chunks:
        logger.warning("embed_chunks called with empty chunks list.")
        return []

    model = _get_model()

    # Filter out invalid chunks
    valid_chunks = []
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            logger.warning(f"Skipping chunk {i}: not a dict.")
            continue
        text = chunk.get("text", "").strip()
        if not text:
            logger.warning(f"Skipping chunk {i}: empty text.")
            continue
        valid_chunks.append((i, chunk, text))

    if not valid_chunks:
        logger.error("No valid chunks to embed.")
        return []

    texts = [text for _, _, text in valid_chunks]

    try:
        logger.info(f"Generating embeddings for {len(texts)} chunk(s)...")
        vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        logger.info(f"Embeddings generated successfully. Dimension: {vectors.shape[1]}")
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise RuntimeError(f"Failed to generate embeddings: {e}") from e

    embedded = []
    for chunk_index, (original_index, chunk, text) in enumerate(valid_chunks):
        chunk_meta = chunk.get("metadata", {})
        section = chunk_meta.get("section_title", chunk_meta.get("section", ""))

        embedded.append({
            "id": str(uuid.uuid4()),
            "text": text,
            "embedding": vectors[chunk_index].tolist(),
            "metadata": {
                "document_name": document_name or chunk_meta.get("file_name", ""),
                "category": category or chunk_meta.get("category", ""),
                "section": section,
                "chunk_index": chunk_index,
            }
        })

    logger.info(f"Embedded {len(embedded)} chunks from '{document_name}'.")
    return embedded


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    sample_chunks = [
        {"text": "This is the introduction section of the proposal.", "metadata": {"section_title": "Introduction"}},
        {"text": "Our proposed solution leverages AI to automate document processing.", "metadata": {"section_title": "Solution"}},
    ]

    results = embed_chunks(sample_chunks, document_name="sample.pdf", category="AI/ML")
    print(f"\nEmbedded {len(results)} chunks.")
    for r in results:
        print(f"  ID: {r['id']} | Section: {r['metadata']['section']} | Dim: {len(r['embedding'])}")
