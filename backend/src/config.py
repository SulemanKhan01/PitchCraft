"""
config.py — Central configuration for PitchCraft backend.

Change any value here ONCE and it automatically applies everywhere.
"""

import os

# ── AI Model ──────────────────────────────────────────────────────────────────
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# ── Vector Search (RAG) ───────────────────────────────────────────────────────
RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.60"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

# ── Proposal Document ─────────────────────────────────────────────────────────
PROPOSAL_TEMPLATE_NAME: str = "AB_Ark_Proposal_Template.docx"
PROPOSAL_LOGO_NAME: str = "image.png"
