import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.services.web_search import search_web, format_web_results_as_context


from sqlalchemy.orm import Session
from database import get_db
from src.models.conversation import Conversation, Message





from fastapi import Depends
# from src.auth.dependencies import get_current_user  # JWT — replaced by Clerk
# from src.models.user import User                    # JWT — replaced by Clerk
from src.auth.clerk_auth import get_current_user_clerk

from src.retrieval.retriever import retrieve_chunks
from src.services.query_betterment import (
    QueryBettermentPipeline,
    ConversationTurn,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Singleton Query Betterment Pipeline
_qb_pipeline = QueryBettermentPipeline()

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None  
    previous_interaction_id: Optional[str] = None
    history: Optional[list[ConversationTurn]] = None
    debug: bool = False


GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "howdy", "yo", "sup",
    "good morning", "good afternoon", "good evening",
    "what's up", "wasup", "whatsup",
}

def _is_greeting(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("?!.,")
    return cleaned in GREETING_WORDS or any(
        cleaned.startswith(w) for w in ("hi ", "hello ", "hey ", "good morning", "good afternoon", "good evening")
    )






def _save_messages_to_db(db: Session,
                        conversation_id: str,
                        user_message: str,
                        assistant_message: str,
                        user_id: str,
                        ):    
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id,
            Conversation.user_id == user_id).first()   
        if not conv:
            return

        if conv.title == "New Conversation":
            conv.title = user_message.strip()[:60]  


        db.add(Message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        ))

        db.add(Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message,
        ))
        db.commit()


    except Exception as e:
        print(f"[DB] Failed to save messages: {e}")
        db.rollback() 





from src.services.chat_agent.pipeline import run_chat_agent


@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user_clerk) , 
                db: Session = Depends(get_db)):

    # ---------------- Greeting Fast-Path ---------------- #

    if _is_greeting(request.question):
        return {"answer": "Hello! How can I help you today?",
                "interaction_id": request.previous_interaction_id
        }

    # ---------------- LangGraph Chat Agent ---------------- #

    result = run_chat_agent(
        question=request.question,
        previous_interaction_id=request.previous_interaction_id,
        history=request.history,
        debug=request.debug,
    )

    answer_text = result.get("answer", "")

    if request.conversation_id and answer_text:
        _save_messages_to_db(
            db=db,
            conversation_id=request.conversation_id,
            user_message=request.question,
            assistant_message=answer_text,
            user_id=current_user.get("sub", "anonymous"),
        )
    return result

