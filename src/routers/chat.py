import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from src.retriever import retrieve_chunks

load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = GEMINI_API_KEY)


router = APIRouter(
    prefix = "/api/chat",
    tags = ["Chat"]
)

class ChatRequest(BaseModel):
    question : str
    # category_filter: str = None


@router.post("/chat")
async def chat(request: ChatRequest):
    chunks = retrieve_chunks(request.question)#,request.category_filter

    if not chunks:
        return {"answer": "I could not find any relevant information in the proposals."}



    context = "\n\n".join([f"[From: {c['document_name']}]\n{c['text']}" for c in chunks])

    prompt = f"""You are a helpful assistant for a proposal management system.
    Answer the user's question ONLY using the context provided below.
    If the answer is not found in the context, say "I don't have that information in the proposals."
    Do NOT make up any information.

    Context:
    {context}

    User Question: {request.question}

    Answer:"""

    response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
    )

    return {"answer": response.text.strip()}
