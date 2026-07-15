import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from the backend/ directory, regardless of CWD
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# --- Qdrant Settings ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pitchcraft_proposals")

# --- Embedding Settings ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIMENSION = 768  # Matches all-MiniLM-L6-v2 output; update if model changes

# EMBEDDING_MODEL = "models/text-embedding-004"
# EMBEDDING_DIMENSION = 768  # Gemini text-embedding-004 output dimension


# --- Chunking Settings ---
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

# --- Pipeline Settings ---
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 64))
PDF_DIR = os.getenv("PDF_DIR", "data/raw_pdfs")
