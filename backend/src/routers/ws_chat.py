import os
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from google import genai
from src.retrieval.retriever import retrieve_chunks
from src.services.query_betterment import QueryBettermentPipeline, ConversationTurn

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

_qb_pipeline = QueryBettermentPipeline()

router = APIRouter(tags=["Chat WebSocket"])


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
   

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            question = data.get("question", "")
            history = data.get("history", [])

            if not question.strip():
                await websocket.send_json({"type": "error", "content": "Empty question"})
                continue

        
            qb_result = _qb_pipeline.run(
                query=question,
                history=history,
                debug_mode=False,
            )

            chunks = retrieve_chunks(qb_result.final_query)

            if not chunks:
                await websocket.send_json({
                    "type": "token",
                    "content": "I could not find any relevant information in the proposals."
                })
                await websocket.send_json({"type": "done"})
                continue

            context = "\n\n".join(
                [f"[From: {c['document_name']}]\n{c['text']}" for c in chunks]
            )

            prompt = f"""You are a helpful assistant for a proposal management system.
            Answer the user's question ONLY using the context provided below.
            If the answer is not found in the context, say "I don't have that information in the proposals."
            Do NOT make up any information.

            Context:
            {context}

            User Question: {question}

            Answer:"""

            stream = client.models.generate_content_stream(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )

            for chunk in stream:
                if chunk.text:
                    await websocket.send_json({
                        "type": "token",
                        "content": chunk.text
                    })

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass