from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Existing routers ──────────────────────────────────────────────────────────
from src.routers import upload
from src.routers import chat
from src.routers import generate_coverletter

# ── New routers ───────────────────────────────────────────────────────────────
from src.routers import conversations
from src.routers import generate_proposal

# ── Database setup ────────────────────────────────────────────────────────────
from database import engine, Base

# Import models so SQLAlchemy registers them before create_all runs
from src.models import user          # existing user model
from src.models import conversation  # new conversation + message models

# Create all tables in PostgreSQL (runs once on startup, safe to run multiple times)
Base.metadata.create_all(bind=engine)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="PitchCraft API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        # Production — server IP (same-origin via Nginx, but kept for safety)
        "http://3.110.54.201",
        "https://3.110.54.201",
        # Add your domain here when ready (Phase 12)
        # "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(generate_coverletter.router)
app.include_router(conversations.router)       # ← NEW
app.include_router(generate_proposal.router)   # ← NEW
# app.include_router(auth.router)  # JWT — replaced by Clerk


@app.get("/")
def read_root():
    return {"msg": "Server is running"}