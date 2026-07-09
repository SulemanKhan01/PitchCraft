# PitchCraft

This project implements a pipeline to process proposal PDFs, extract text, categorize them using an LLM, chunk the text, embed the chunks, and store them in Qdrant.

## File Structure

```
PitchCraft/
├── data/
│   ├── raw_pdfs/                     # All original proposal PDFs (unsorted, as-is)
│   │   ├── proposal_001.pdf
│   │   ├── proposal_002.pdf
│   │   └── ...
│   │
│   └── processed/
│       ├── tagged_proposals.json     # Extracted text + LLM-assigned category, per proposal
│       └── chunked_proposals.json    # Final chunks + metadata (ready for embedding)
│
├── src/
│   ├── extractor.py                  # PDF → raw text (pdfplumber)
│   ├── categorizer.py                # Text → category tags (LLM call)
│   ├── chunker.py                    # Text → section-based chunks (with fallback for long sections)
│   ├── embedder.py                   # Chunk → vector (sentence-transformers)
│   ├── vector_store.py               # Qdrant setup + upsert logic
│   └── pipeline.py                   # Runs all steps in order, one PDF at a time
│
├── config.py                          # Settings: chunk size, model names, Qdrant path, etc.
├── run.py                             # Entry point — just run this to process all PDFs
├── requirements.txt
├── .env                               # API keys (never commit)
└── README.md
```