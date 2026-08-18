"""
config.py — Central configuration for PitchCraft backend.

Change any value here ONCE and it automatically applies everywhere.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
# Automatically load backend/.env file regardless of how Python is executed
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ── AI Model ──────────────────────────────────────────────────────────────────
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
NETLIFY_AUTH_TOKEN: str = os.getenv("NETLIFY_AUTH_TOKEN", "")


_gemini_client: genai.Client | None = None
def get_gemini_client() -> genai.Client:
    """
    Returns a shared, lazy-loaded instance of the Gemini API Client.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client




# ── Vector Search (RAG) ───────────────────────────────────────────────────────
RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.60"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

# ── Proposal Document ─────────────────────────────────────────────────────────
PROPOSAL_TEMPLATE_NAME: str = "AB_Ark_Proposal_Template.docx"
PROPOSAL_LOGO_NAME: str = "image.png"
