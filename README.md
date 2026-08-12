# PitchCraft 🚀

An **Enterprise-Grade AI-Powered Proposal & Cover Letter Generation Platform** with a **Production RAG (Retrieval-Augmented Generation)** architecture, multi-agent workflows via **LangGraph**, vector search with **Qdrant**, web search fallback via **Tavily**, and dynamic **DOCX / PDF document generation**.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [AI / RAG Pipeline](#ai--rag-pipeline)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Performance & Optimization](#performance--optimization)
- [Error Handling & Reliability](#error-handling--reliability)
- [Deployment](#deployment)
- [Presentation Summary](#presentation-summary)

---

## Project Overview

**PitchCraft** solves the critical operational bottleneck faced by software agencies, enterprise sales teams, and freelancers: the manual, time-consuming process of tailoring technical proposals and job-specific cover letters for prospective clients.

### Problem Statement
Crafting high-converting technical proposals and client cover letters requires analyzing client requirements, retrieving past project case studies, organizing technical architecture stacks, estimating project pricing and timelines, and formatting documents professionally. Doing this manually for every lead takes hours and leads to inconsistent quality.

### Solution & Key Capabilities
PitchCraft automates this entire pipeline using state-of-the-art AI orchestration:
1. **Document Knowledge Ingestion**: Extracts, categorizes, chunks, embeds, and indexes past proposal PDFs and agency knowledge into Qdrant vector databases.
2. **Context-Aware RAG Chat Agent**: Allows users to interactively query indexed agency proposals and past client engagements.
3. **Streamlined Query Betterment**: Pre-processes user queries via a consolidated single-LLM stage for intent classification, technical keyword extraction, and contextual query rewriting.
4. **LangGraph Multi-Agent Workflows**: Employs deterministic state graphs for query routing, job description parsing, smart retrieval, market context search, and document generation.
5. **Automated Proposal Generation**: Generates 8-11 page technical proposals in parallel and compiles them into branded `.docx` documents matching enterprise design templates (cover pages, phase banners, styled tables, headers, and footers).
6. **Tailored Cover Letter Engine**: Parses client Job Descriptions (JDs) into structured criteria, retrieves matching agency proof points, and generates structured cover letters with `.docx` and `.pdf` downloads.

---

## Features

### 📄 1. Document Upload & Multi-Collection Ingestion
- Upload PDF proposals and agency knowledge directly through the UI or batch CLI tools.
- Automated extraction via `pdfplumber`, text categorization using Gemini LLM, semantic chunking, and vector embedding using `gemini-embedding-2`.
- Direct storage into target Qdrant collections (`pitchcraft_cover_letter_kb` & `pitchcraft_proposals_kb`).

### 💬 2. RAG Chat System with Intent & Context Fusion
- **Session Management**: Persistent chat conversations stored in SQLite / PostgreSQL via SQLAlchemy.
- **Greeting Fast-Path**: Instant low-latency responses for simple greeting queries.
- **Conversational Pronoun Resolution**: Resolves context and pronouns (e.g., *"What about the second one?"*) from past turns.
- **Unified Query Enricher**: A consolidated single master LLM call replacing 7 separate stages to optimize queries while preserving high throughput.

### 🌐 3. Hybrid Web Search Fallback (Tavily AI)
- If vector retrieval produces chunks below relevance threshold (`score < 0.60`), the system automatically routes to Tavily AI Web Search.
- Fetches real-time web context, formats search results, and cites sources naturally in the final answer.

### 📑 4. Multi-Agent Proposal Generation
- **LangGraph Workflow**:
  - `analyze_chat_node`: Extracts structured project requirements (title, client name, tech stack, scope, budget, timeline) from chat history.
  - `web_search_node`: Queries real-time market data for technology pricing and architectural estimates.
  - `write_proposal_node`: Executes a parallel multi-section generator using `ThreadPoolExecutor` to author an 8–10 section technical proposal in Markdown.
- **Enterprise DOCX Builder**: Compiles Markdown proposals into formatted Word documents with cover pages, section headers, phase banners, and styled table layouts.

### ✉️ 5. Automated Cover Letter Generator
- **JD Parser**: Extracts project title, required skills, scope of work, industry domain, and pain points.
- **Smart Retriever**: Executes targeted queries against Qdrant, de-duplicates chunks, and ranks top evidence points.
- **Multi-Format Export**: One-click download of cover letters in `.docx` and minimal styled `.pdf` formats.

### 🔐 6. Authentication & User Management
- Integrated **Clerk Authentication** (`clerk_auth.py`) with session JWT verification via Clerk JWKS public keys.
- Automatic key rotation handling and local dev fallback mode for offline testing.

---

## System Architecture

```text
                               ┌───────────────────────────┐
                               │        User / UI          │
                               └─────────────┬─────────────┘
                                             │ HTTP Requests
                                             ▼
                               ┌───────────────────────────┐
                               │   FastAPI Backend API     │
                               │  (Routers: Chat, Upload,  │
                               │   CoverLetter, Proposal)  │
                               └─────────────┬─────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               │                             │                             │
               ▼                             ▼                             ▼
   ┌───────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
   │ Query Betterment      │   │ LangGraph Workflows      │   │ Database (SQLAlchemy)    │
   │ - Context Resolution  │   │ - Chat Agent Graph       │   │ - Conversations Table    │
   │ - Unified Enrichment  │   │ - Cover Letter Graph     │   │ - Messages Table         │
   └───────────┬───────────┘   │ - Proposal Generator     │   └──────────────────────────┘
               │               └─────────────┬────────────┘
               ▼                             │
   ┌───────────────────────┐                 │
   │ Gemini Embedding      │                 │
   │ (gemini-embedding-2)  │                 │
   └───────────┬───────────┘                 │
               │                             │
               ▼                             ▼
   ┌───────────────────────┐   ┌──────────────────────────┐
   │ Qdrant Vector Store   │   │ Tavily Web Search        │
   │ (Parallel Multi-Col)  │   │ (Low-Score Fallback)     │
   └───────────┬───────────┘   └─────────────┬────────────┘
               │                             │
               └──────────────┬──────────────┘
                              │ Context & Evidence
                              ▼
               ┌───────────────────────────┐
               │ Google Gemini LLM Engine  │
               │ (gemini-3.1-flash-lite /  │
               │  gemini-2.5-flash)        │
               └──────────────┬────────────┘
                              │ Response / Content
                              ▼
               ┌───────────────────────────┐
               │ Export Engine             │
               │ - Python-Docx Builder     │
               │ - ReportLab PDF Engine    │
               └───────────────────────────┘
```

---

## AI / RAG Pipeline

```text
User Question / Chat History
             │
             ▼
[Stage 0: Conversation Context] ── (Resolves pronouns & follow-ups using chat history)
             │
             ▼
[Stage 1: Unified Query Enricher] ── (Fixes typos, detects intent, extracts keywords in 1 LLM call)
             │
             ▼
[Stage 2: Gemini Embeddings] ── (Generates 768-dim query vector using gemini-embedding-2)
             │
             ▼
[Stage 3: Parallel Vector Search] ── (ThreadPoolExecutor queries Qdrant collections simultaneously)
             │
      ┌──────┴─────────────────────────────────┐
      │ Score >= 0.60                          │ Score < 0.60 (Fallback)
      ▼                                        ▼
[Vector Chunks Context]               [Stage 3.5: Tavily Web Search]
      │                                        │ (Fetches market data & context)
      │                                        │
      └───────────────────┬────────────────────┘
                          │
                          ▼
            [Stage 4: Gemini LLM Synthesis]
                          │
                          ▼
             Final Answer / Streamed Output
```

---

## Technology Stack

### Frontend
- **Framework**: React 19, Vite
- **Routing & State**: React Router v7, Zustand
- **Icons & Styling**: Lucide React, Vanilla CSS design tokens
- **Auth Client**: Clerk React SDK (`@clerk/clerk-react`)

### Backend & API
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn
- **ORM & Database**: SQLAlchemy 2.0 (SQLite / PostgreSQL)
- **Data Validation**: Pydantic v2
- **Auth Verification**: Python-Jose (Clerk JWT & JWKS verification)

### AI / ML & RAG Orchestration
- **Agent Framework**: LangGraph, LangChain Core
- **LLM Engine**: Google GenAI SDK (`google-genai`), Gemini 3.1 Flash Lite / Gemini 2.5 Flash
- **Embeddings**: `gemini-embedding-2` (768-dimensional vectors)
- **Vector Database**: Qdrant (`qdrant-client`)
- **Web Search**: Tavily AI (`tavily-python`)

### Document Processing & Export
- **PDF Extraction**: `pdfplumber`
- **DOCX Generator**: `python-docx`, `docxtpl`, `docxcompose`
- **PDF Generator**: `reportlab`

---

## Project Structure

```text
PitchCraft/
├── backend/
│   ├── main.py                               # FastAPI application entry point
│   ├── run.py                                # Ingestion CLI tool for batch PDF processing
│   ├── config.py                             # Central backend configuration settings
│   ├── database.py                           # SQLAlchemy database connection & session setup
│   ├── requirements.txt                      # Python dependencies (UTF-8)
│   ├── .env.example                          # Backend environment variables template
│   ├── pitchcraft.db                         # SQLite local database instance
│   ├── data/
│   │   ├── raw_pdfs/                         # Input directory for proposal PDFs
│   │   └── processed/                        # Categorized proposal JSON output
│   └── src/
│       ├── auth/                             # Authentication dependencies
│       │   ├── clerk_auth.py                 # Clerk JWT & JWKS validation logic
│       │   └── dependencies.py               # Legacy JWT auth helpers
│       ├── chunking/
│       │   └── chunker.py                    # Semantic text chunking engine
│       ├── extraction/
│       │   └── extractor.py                  # pdfplumber text extraction
│       ├── embeddings/
│       │   └── embedder.py                   # Gemini vector embedding generator
│       ├── models/                           # SQLAlchemy database schema models
│       │   ├── conversation.py               # Conversation & Message DB tables
│       │   └── user.py                       # User table schema
│       ├── pipeline/                         # Ingestion pipeline graph & nodes
│       │   ├── graph.py                      # LangGraph ingestion state graph
│       │   ├── nodes.py                      # Ingestion execution nodes
│       │   └── pipeline.py                   # Public process_pdf() entrypoint
│       ├── retrieval/
│       │   ├── retriever.py                  # Parallel Qdrant search retriever
│       │   └── vector_store.py               # Qdrant client connection & upsert logic
│       ├── routers/                          # FastAPI API endpoint modules
│       │   ├── chat.py                       # POST /api/chat/chat
│       │   ├── conversations.py              # GET/POST/DELETE /api/conversations/
│       │   ├── generate_coverletter.py       # POST /api/generate/cover-letter (PDF/DOCX)
│       │   ├── generate_proposal.py          # POST /api/generate/proposal (DOCX)
│       │   └── upload.py                     # POST /api/proposals/upload
│       └── services/
│           ├── categorizer.py                # LLM document classification
│           ├── web_search.py                 # Tavily search wrapper & formatter
│           ├── chat_agent/                   # LangGraph RAG Chat Agent
│           │   ├── graph.py                  # StateGraph definition with conditional routing
│           │   ├── nodes.py                  # Chat execution nodes
│           │   ├── pipeline.py               # run_chat_agent() runner
│           │   └── state.py                  # ChatAgentState schema
│           ├── cover_letter/                 # Cover Letter Generation Pipeline
│           │   ├── content_generator.py      # Gemini text generator
│           │   ├── docx_generator.py         # DOCX document builder
│           │   ├── graph.py                  # Cover letter state graph
│           │   ├── jd_parser.py              # Structured Job Description parser
│           │   ├── nodes.py                  # Execution nodes
│           │   ├── pdf_generator.py          # ReportLab PDF builder
│           │   ├── pipeline.py               # Entrypoint wrapper
│           │   └── smart_retriever.py        # Evidence chunk retriever
│           ├── proposal_generator/           # Enterprise Proposal Generation Pipeline
│           │   ├── chat_analyzer.py          # Requirement extraction node
│           │   ├── docx_generator.py         # Master DOCX layout builder
│           │   ├── header_footer.py          # Header, footer, & pagination engine
│           │   ├── proposal_writer.py        # Parallel multi-section generator
│           │   └── styles.py                 # Corporate typography & colors
│           └── query_betterment/             # Query Betterment Subsystem
│               ├── conversation_context.py   # Turn history & pronoun fusion
│               ├── pipeline.py               # QueryBettermentPipeline orchestrator
│               └── unified_enricher.py       # Single-call LLM enrichment module
│
├── frontend/
│   ├── index.html                            # HTML entry point
│   ├── package.json                          # Node.js dependencies & scripts
│   ├── vite.config.js                        # Vite build configuration
│   ├── .env.production                       # Production frontend environment configuration
│   └── src/
│       ├── App.jsx                           # Application routing container
│       ├── main.jsx                          # React application root
│       ├── components/                       # UI components (Layout, Sidebar, Auth)
│       ├── pages/                            # Main application pages
│       │   ├── ChatPage.jsx                  # Interactive RAG chat interface
│       │   ├── CoverLetterPage.jsx           # Cover letter generator interface
│       │   ├── UploadPage.jsx                # Document upload interface
│       │   └── SettingsPage.jsx              # System settings interface
│       ├── services/
│       │   └── api.js                        # Unified frontend REST API client
│       └── stores/                           # Zustand state management stores
│
├── requirements.txt                          # Main unified Python requirements (UTF-8)
└── README.md                                 # Technical documentation
```

---

## API Documentation

### 1. Proposal Knowledge Base Upload
- **Method**: `POST`
- **Route**: `/api/proposals/upload`
- **Parameters**: `file` (Multipart PDF), `target_collection` (Query param: `cover_letter` or `proposal`)
- **Response**: `{ "message": "Success! File processed.", "filename": "...", "category": "...", "chunks_created": 12 }`

### 2. RAG Chat Endpoint
- **Method**: `POST`
- **Route**: `/api/chat/chat`
- **Request Body**:
  ```json
  {
    "question": "What is our experience with AWS SageMaker?",
    "conversation_id": "optional-uuid",
    "previous_interaction_id": "optional-id",
    "history": [],
    "debug": false
  }
  ```
- **Response**: `{ "answer": "...", "interaction_id": "...", "source": "rag" | "web_search" | "gemini_knowledge" }`

### 3. Conversation Management
- **`POST /api/conversations/`**: Creates a new session ID.
- **`GET /api/conversations/`**: Returns all past user conversation sessions for sidebar display.
- **`GET /api/conversations/{id}`**: Fetches a full conversation thread and message history.
- **`DELETE /api/conversations/{id}`**: Deletes a conversation session.

### 4. Enterprise Proposal Document Generation
- **`POST /api/generate/proposal`**: Analyzes chat session messages, performs market search, and returns generated proposal content JSON and extracted requirements.
- **`POST /api/generate/proposal/docx`**: Renders and streams the official AB {Ark} `.docx` proposal binary document.

### 5. Cover Letter Generation
- **`POST /api/generate/cover-letter`**: Accepts `jd_text`, parses criteria, searches vector store, and returns generated cover letter text.
- **`POST /api/generate/cover-letter/pdf`**: Streams generated cover letter as styled PDF.
- **`POST /api/generate/cover-letter/docx`**: Streams generated cover letter as DOCX file.

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and `npm`
- Docker (for Qdrant vector database)
- Google Gemini API Key

---

### Step 1: Clone Repository
```bash
git clone https://github.com/SulemanKhan01/PitchCraft.git
cd PitchCraft
```

---

### Step 2: Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv backend\venv
   .\backend\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv backend/venv
   source backend/venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=
   DATABASE_URL=sqlite:///./pitchcraft.db
   ```

---

### Step 3: Vector Database Setup
Run Qdrant via Docker:
```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

---

### Step 4: Batch Ingest Proposals (Optional)
Drop proposal PDFs into `backend/data/raw_pdfs/` and run the ingestion CLI:
```bash
cd backend
python run.py
```

---

### Step 5: Start Backend API Server
Run Uvicorn from the `backend/` directory:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
> **Note**: Do NOT run `uvicorn app.main:app`. The main application script is `main.py` inside `backend/`.

---

### Step 6: Frontend Setup
1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open browser at `http://localhost:5173`.

---

## Configuration

### Backend Environment Variables (`backend/.env`)
| Variable | Default Value | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | *Required* | API key for Gemini LLM and Embedding models |
| `TAVILY_API_KEY` | *Optional* | API key for Tavily Web Search fallback |
| `QDRANT_URL` | `http://localhost:6333` | Host URL for Qdrant Vector DB |
| `COLLECTION_NAME` | `pitchcraft_cover_letter_kb` | Main collection name for cover letter evidence |
| `PROPOSAL_KB_COLLECTION` | `pitchcraft_proposals_kb` | Collection name for proposal knowledge base |
| `EMBEDDING_MODEL` | `gemini-embedding-2` | Model name for vector embeddings |
| `DATABASE_URL` | `sqlite:///./pitchcraft.db` | Database connection string (SQLite or PostgreSQL) |

### Frontend Environment Variables (`frontend/.env`)
| Variable | Value | Purpose |
|---|---|---|
| `VITE_API_BASE` | `http://localhost:8000` | Base URL of FastAPI server |
| `VITE_CLERK_PUBLISHABLE_KEY` | `pk_test_...` | Clerk Authentication publishable key |

---

## Usage

1. **Ingest Proposals**: Upload past proposals via `/upload` view to populate your Qdrant vector database.
2. **RAG Chat**: Ask technical questions in `/chat`. The system resolves context, queries Qdrant, and falls back to Tavily web search if extra information is needed.
3. **Generate Technical Proposal**: Discuss project requirements in chat, then click **Generate Proposal**. PitchCraft analyzes the full context and outputs an 8-11 page structured proposal available for download as `.docx`.
4. **Generate Cover Letter**: Paste a job description in `/cover-letter`. PitchCraft parses criteria, retrieves past evidence, and generates a cover letter ready for PDF/DOCX download.

---

## Performance & Optimization

- **Parallel Vector Retrieval**: Queries multiple Qdrant collections concurrently using `ThreadPoolExecutor` in `retriever.py`.
- **Parallel Multi-Section Document Writing**: `proposal_writer.py` generates 8-10 proposal sections in parallel (max 5 worker threads), slashing proposal generation time.
- **Consolidated Single-Call Query Enricher**: Replaced a multi-step sequential LLM pipeline with a structured single master LLM call (`unified_enricher.py`).
- **Clerk JWKS In-Memory Caching**: `clerk_auth.py` caches public RSA signing keys in memory to minimize external network latency on requests.

---

## Error Handling & Reliability

- **Retriever Threshold Fallback**: If vector search confidence scores fall below `0.60`, the system automatically shifts to Tavily Web Search rather than returning irrelevant text.
- **Outline & Section Fallbacks**: If LLM output fails during section generation, default proposal structures and fallback blocks are injected so document building never crashes.
- **Clerk Offline Dev Fallback**: Unauthenticated local requests gracefully fallback to a standard development user identity (`local-dev-user`).

---

## Deployment

### Production Nginx Reverse Proxy Setup
In production, Nginx proxies API traffic from `/api/*` to the FastAPI backend running on port 8000:
```nginx
server {
    listen 80;
    server_name 3.110.54.201;

    location / {
        root /var/www/pitchcraft/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Presentation Summary

### Problem
Manual proposal writing and cover letter drafting for software projects is slow, repetitive, and inconsistent, wasting valuable sales and engineering time.

### Solution
An enterprise AI platform that ingests past proposals into Qdrant vector databases, uses LangGraph multi-agent workflows to analyze client requirements, performs market research via Tavily, and automatically generates formatted `.docx` and `.pdf` technical proposals and cover letters.

### Key Features
- Multi-Collection Qdrant Vector Retrieval with parallel querying.
- LangGraph Workflows for Chat RAG, Proposal Generation, and Cover Letter parsing.
- Tavily Web Search fallback when vector store scores are low.
- Consolidated Query Betterment pipeline.
- Custom enterprise `.docx` engine (cover pages, headers/footers, styled tables).
- Clerk JWT authentication with JWKS caching.

### Architecture
`Frontend (React/Vite)` ➔ `Backend (FastAPI)` ➔ `LangGraph Agents` ➔ `Qdrant / Tavily` ➔ `Gemini LLM` ➔ `DOCX/PDF Exporters`

### AI/RAG Workflow
Query ➔ Context Fusion ➔ Unified Enrichment ➔ Vector Search (Qdrant) ➔ Relevance Threshold Check (Score >= 0.60) ➔ [If low: Web Search Fallback] ➔ Gemini LLM Synthesis ➔ Response / Document Export.

### Technology Stack
Python FastAPI, React 19, Vite, LangGraph, Qdrant, Google Gemini LLM (`gemini-embedding-2`, `gemini-3.1-flash-lite`), Tavily Web Search, Python-Docx, ReportLab, Clerk Auth.

### Key Technical Contributions
1. **Parallelized Multi-Section LLM Generation**: Uses `ThreadPoolExecutor` to generate multi-page proposal sections in parallel.
2. **Deterministic Hybrid Fallback Routing**: Seamless transition between vector store retrieval and live Tavily web search.
3. **Enterprise Template Engine**: Full programmatic `.docx` layout generation matching branded proposal designs.

### Implemented vs Planned Work
- **Implemented**: Full PDF ingestion, multi-collection Qdrant search, single-call query enrichment, LangGraph RAG chat agent, Tavily search fallback, cover letter generator, multi-section proposal generator, DOCX/PDF export engines, session history in DB, Clerk auth integration.
- **Planned / Future Improvements**:
  - Live streaming (SSE/WebSocket) for real-time section generation feedback.
  - Multi-tenant workspace separation within Qdrant payload filters.
  - Automated budget calculation engine based on historical milestone data.