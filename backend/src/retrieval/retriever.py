import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.retrieval.vector_store import _get_client
from config import TARGET_COLLECTIONS, COLLECTION_NAME

load_dotenv()

logger = logging.getLogger("retriever")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def _search_single_collection(collection_name: str, query_vector: list, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Helper function: Queries a single Qdrant collection using a pre-computed embedding vector.
    Runs inside a thread worker.
    """
    try:
        qdrant = _get_client()
        response = qdrant.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
        )
        points = response.points

        chunks = []
        for p in points:
            chunks.append({
                "text": p.payload.get("text", ""),
                "document_name": p.payload.get("document_name", "Unknown"),
                "category": p.payload.get("category", "General"),
                "collection": collection_name,  # Tracks source collection
                "score": p.score,
            })
        return chunks
    except Exception as exc:
        logger.warning(f"Failed to query collection '{collection_name}': {exc}")
        return []


def retrieve_chunks(
    query: str,
    target_collections: Optional[List[str]] = None,
    limit_per_collection: int = 5,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieves relevant proposal/cover-letter chunks from multiple Qdrant vector collections
    IN PARALLEL using ThreadPoolExecutor.

    Args:
        query: User query string.
        target_collections: List of collection names to search. Defaults to TARGET_COLLECTIONS.
        limit_per_collection: Max chunks to fetch from EACH collection (default 5).
        top_k: Final number of top-ranked chunks to return after merging (default 5).

    Returns:
        Sorted, deduplicated list of chunk dicts with highest scores first.
    """
    if target_collections is None:
        target_collections = TARGET_COLLECTIONS

    # 1. Generate Query Vector Embedding (Done ONCE for all collections)
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    query_vector = response.embeddings[0].values

    # 2. Parallel Querying with ThreadPoolExecutor
    all_chunks = []
    max_workers = len(target_collections)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit search tasks to the thread pool for all target collections
        future_to_col = {
            executor.submit(
                _search_single_collection, col, query_vector, limit_per_collection
            ): col
            for col in target_collections
        }

        # Collect results as threads complete
        for future in as_completed(future_to_col):
            col_name = future_to_col[future]
            try:
                result_chunks = future.result()
                all_chunks.extend(result_chunks)
            except Exception as exc:
                logger.error(f"Error fetching results from '{col_name}': {exc}")

    # 3. Deduplicate Chunks (if exact same text exists in multiple collections)
    unique_chunks = {}
    for chunk in all_chunks:
        key = chunk["text"].strip()
        if key not in unique_chunks or chunk["score"] > unique_chunks[key]["score"]:
            unique_chunks[key] = chunk

    # 4. Sort All Combined Chunks by Score (Highest Relevance First)
    sorted_chunks = sorted(unique_chunks.values(), key=lambda x: x["score"], reverse=True)

    # 5. Return Top K chunks
    return sorted_chunks[:top_k]
