from typing import Collection
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .vector_store import _get_client

load_dotenv()
from config import COLLECTION_NAME

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = GEMINI_API_KEY)


def retrieve_chunks(query:str ):

# , category_filter: str = None
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents= query,  
        config=types.EmbedContentConfig(output_dimensionality=768)
    )

    query_vector = response.embeddings[0].values

    qdrant = _get_client()

    # search_filter = None
    # if category_filter:
    #     from qdrant_client.models import Filter, FieldCondition, MatchValue
    #     search_filter = Filter(
    #         must=[FieldCondition(key="category", match=MatchValue(value=category_filter))]
    #     )

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=5,
        # query_filter=search_filter,
    ).points

    # return results

    chunks = []
    for result in results:
        chunks.append({
            "text": result.payload["text"],
            "document_name": result.payload["document_name"],
            # "category": result.payload["category"],
            "score": result.score,
        })

    return chunks


test = retrieve_chunks("tell me somthing about Edge-Based Computer Vision (CV) Pipeline")
print(test)
# # chunk = test[0]
# # print(chunk['text'])