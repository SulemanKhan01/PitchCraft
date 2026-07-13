# PitchCraft 🚀

A **Production-Grade RAG (Retrieval-Augmented Generation) System** for processing,
indexing, and intelligently querying proposal PDFs.

---

## System Architecture

```
User Query
    │
    ▼
Query Betterment Pipeline   ← NEW (pre-embedding enrichment)
    │  • Spell Correction
    │  • Intent Detection
    │  • Query Rewriting
    │  • Query Expansion
    │  • Multi-Query Generation
    │  • Keyword Extraction
    ▼
Embedding Model (Gemini gemini-embedding-2)
    │
    ▼
Qdrant Vector Store  →  Top-K Relevant Chunks
    │
    ▼
LLM Answer Generation (Gemini Flash Lite)
```

---

## Project Structure

```
PitchCraft/
│
├── data/
│   ├── raw_pdfs/                         # Drop your proposal PDFs here
│   └── processed/
│       └── tagged_proposals.json         # LLM-assigned categories (auto-generated)
│
├── src/
│   │
│   ├── routers/                          # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── upload.py                     # POST /api/upload  — ingest a new PDF
│   │   └── chat.py                       # POST /api/chat/chat — ask a question
│   │
│   ├── query_betterment/                 # Query Betterment Pipeline (pre-embedding)
│   │   ├── __init__.py                   # Public API: QueryBettermentPipeline
│   │   ├── models.py                     # All Pydantic data contracts
│   │   ├── utils.py                      # Gemini client factory, timer, JSON parser
│   │   ├── logger.py                     # Structured JSON stage logger
│   │   ├── confidence.py                 # Weighted confidence aggregation
│   │   ├── conversation_context.py       # Phase 0 — pronoun / follow-up resolver
│   │   ├── spell_corrector.py            # Stage 1 — typo / OCR / grammar fixes
│   │   ├── intent_detector.py            # Stage 2 — 13-class intent taxonomy
│   │   ├── query_rewriter.py             # Stage 3 — retrieval-friendly rewriting
│   │   ├── query_expander.py             # Stage 4 — synonym / alias expansion
│   │   ├── multi_query.py                # Stage 5 — semantic variant generation
│   │   ├── keyword_extractor.py          # Stage 6 — technical NER (9 categories)
│   │   └── pipeline.py                   # Orchestrator — chains all stages
│   │
│   ├── __init__.py
│   ├── extractor.py                      # PDF → raw text  (pdfplumber)
│   ├── categorizer.py                    # Text → category tag  (Gemini LLM)
│   ├── chunker.py                        # Text → semantic chunks
│   ├── embedder.py                       # Chunk → vector  (Gemini Embedding)
│   ├── vector_store.py                   # Qdrant client + upsert logic
│   ├── pipeline.py                       # Ingestion pipeline: PDF → Qdrant
│   └── test.py                           # Quick manual test script
│
├── config.py                             # Central settings (chunk size, model, Qdrant URL)
├── main.py                               # FastAPI app entry point
├── run.py                                # CLI: batch-process all PDFs in data/raw_pdfs/
├── requirement.txt                       # Python dependencies
├── .env                                  # Secrets — NEVER commit  (see .env.example)
├── .env.example                          # Template — copy to .env and fill in values
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone & set up environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirement.txt
```

### 2. Configure environment variables

```bash
copy .env.example .env         # Windows
# Open .env and fill in GEMINI_API_KEY, QDRANT_URL, etc.
```

### 3. Start Qdrant (Docker)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Ingest PDFs

Drop your proposal PDFs into `data/raw_pdfs/`, then run:

```bash
python run.py
```

This executes the full ingestion pipeline:
```
PDF → Extract Text → Categorize → Chunk → Embed → Store in Qdrant
```

### 5. Start the API server

```bash
uvicorn main:app --reload
```

---

## API Endpoints

### `POST /api/upload`
Upload and process a new PDF proposal.

### `POST /api/chat/chat`
Ask a question against the indexed proposals.

**Minimal request:**
```json
{ "question": "What is the budget for the Edge-CV proposal?" }
```

**With conversation history (follow-up resolution):**
```json
{
  "question": "What about the second one?",
  "history": [
    { "role": "user",      "content": "What AI proposals do we have?" },
    { "role": "assistant", "content": "We have three AI/ML proposals..." }
  ]
}
```

**With full debug trace:**
```json
{
  "question": "tell me somthing about Edge-Basd CV Pipline",
  "debug": true
}
```

Debug response includes per-stage input/output, latency, confidence, and the
fully enriched `final_query` sent to the retriever.

---

## Query Betterment Pipeline

Every query passes through 6 enrichment stages **before** it reaches the
embedding model:

| Stage | Module | Responsibility |
|---|---|---|
| Phase 0 | `conversation_context` | Resolve pronouns & follow-up references |
| Stage 1 | `spell_corrector`      | Fix typos, OCR errors, grammar mistakes |
| Stage 2 | `intent_detector`      | Classify into 13-class intent taxonomy |
| Stage 3 | `query_rewriter`       | Rewrite for retrieval precision |
| Stage 4 | `query_expander`       | Add synonyms, aliases, related concepts |
| Stage 5 | `multi_query`          | Generate semantic query variants |
| Stage 6 | `keyword_extractor`    | Extract technical named entities |

Every stage logs input, output, latency, and confidence.
Any stage failure degrades gracefully — the pipeline never crashes.

---

## Configuration (`config.py`)

| Variable | Default | Description |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `COLLECTION_NAME` | `pitchcraft_proposals` | Qdrant collection name |
| `EMBEDDING_MODEL` | `gemini-embedding-2` | Gemini embedding model |
| `EMBEDDING_DIMENSION` | `768` | Vector dimension |
| `MAX_CHUNK_SIZE` | `500` | Max tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `BATCH_SIZE` | `64` | Qdrant upsert batch size |
| `PDF_DIR` | `data/raw_pdfs` | PDF input directory |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| LLM & Embeddings | Google Gemini (gemini-3.1-flash-lite + gemini-embedding-2) |
| Vector Database | Qdrant |
| PDF Extraction | pdfplumber |
| Data Validation | Pydantic v2 |
| Environment | python-dotenv |