import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME,
    EMBEDDING_DIMENSION,
    BATCH_SIZE,
)

logger = logging.getLogger("vector_store")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[VectorStore] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False


def _get_client():
    """Create and return a Qdrant client, raising a clear error if unavailable."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30,
        )
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant at '{QDRANT_URL}': {e}")
        raise ConnectionError(f"Cannot connect to Qdrant: {e}") from e


def ensure_collection(client=None, collection_name: str = COLLECTION_NAME, vector_dim: int = EMBEDDING_DIMENSION):
    """
    Create the Qdrant collection if it does not exist.
    Does NOT recreate the collection if it already exists.
    """
    from qdrant_client.models import Distance, VectorParams

    if client is None:
        client = _get_client()

    try:
        existing = [c.name for c in client.get_collections().collections]
        if collection_name in existing:
            logger.info(f"Collection '{collection_name}' already exists. Skipping creation.")
        else:
            logger.info(f"Creating collection '{collection_name}' with dim={vector_dim}...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
    except Exception as e:
        logger.error(f"Failed to ensure collection '{collection_name}': {e}")
        raise RuntimeError(f"Collection setup failed: {e}") from e

    return client


def upsert_vectors(
    embedded_chunks: list[dict],
    collection_name: str = COLLECTION_NAME,
    batch_size: int = BATCH_SIZE,
) -> int:
    """
    Upsert embedded chunks into Qdrant in batches.

    Args:
        embedded_chunks: List of dicts from embed_chunks(), each with:
            'id', 'text', 'embedding', 'metadata' (document_name, category, section, chunk_index)
        collection_name: Target Qdrant collection.
        batch_size: Number of vectors to upsert per batch.

    Returns:
        Number of successfully upserted vectors.
    """
    from qdrant_client.models import PointStruct

    if not embedded_chunks:
        logger.warning("upsert_vectors called with empty list.")
        return 0

    client = _get_client()
    ensure_collection(client, collection_name)

    total_upserted = 0

    for batch_start in range(0, len(embedded_chunks), batch_size):
        batch = embedded_chunks[batch_start: batch_start + batch_size]
        points = []

        for item in batch:
            try:
                meta = item.get("metadata", {})
                point = PointStruct(
                    id=item["id"],
                    vector=item["embedding"],
                    payload={
                        "text": item["text"],
                        "document_name": meta.get("document_name", ""),
                        "category": meta.get("category", ""),
                        "section": meta.get("section", ""),
                        "chunk_index": meta.get("chunk_index", 0),
                    },
                )
                points.append(point)
            except Exception as e:
                logger.warning(f"Skipping malformed chunk (id={item.get('id', '?')}): {e}")

        if not points:
            continue

        try:
            client.upsert(collection_name=collection_name, points=points, wait=True)
            total_upserted += len(points)
            logger.info(
                f"Upserted batch [{batch_start + 1}–{batch_start + len(points)}] "
                f"({len(points)} vectors) into '{collection_name}'."
            )
        except Exception as e:
            logger.error(f"Batch upsert failed (batch starting at {batch_start}): {e}")
            raise RuntimeError(f"Qdrant upsert failed: {e}") from e

    logger.info(f"Total vectors upserted: {total_upserted}")
    return total_upserted


if __name__ == "__main__":
    # Quick smoke test: insert two fake vectors
    import uuid

    fake_dim = EMBEDDING_DIMENSION
    fake_chunks = [
        {
            "id": str(uuid.uuid4()),
            "text": "Hello world chunk.",
            "embedding": [0.0] * fake_dim,
            "metadata": {
                "document_name": "test.pdf",
                "category": "Test",
                "section": "Intro",
                "chunk_index": 0,
            },
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Another test chunk.",
            "embedding": [0.1] * fake_dim,
            "metadata": {
                "document_name": "test.pdf",
                "category": "Test",
                "section": "Body",
                "chunk_index": 1,
            },
        },
    ]

    print(f"Connecting to Qdrant at: {QDRANT_URL}")
    n = upsert_vectors(fake_chunks)
    print(f"Upserted {n} test vectors into '{COLLECTION_NAME}'.")
