"""
run.py — Entry point for PitchCraft.

Scans data/raw_pdfs/ for all PDF files and runs the full pipeline
(Extract → Categorize → Chunk → Embed → Store in Qdrant) on each one.
"""
import os
import sys

# Make sure src/ and the project root are on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_DIR)

from config import PDF_DIR, COLLECTION_NAME
from src.pipeline.pipeline import process_pdf


def main():
    pdf_folder = os.path.join(PROJECT_ROOT, PDF_DIR)

    print("=" * 50)
    print("  PitchCraft — Proposal Processing Pipeline")
    print("=" * 50)
    print(f"  PDF folder : {pdf_folder}")
    print(f"  Collection : {COLLECTION_NAME}")
    print("=" * 50)

    # ── Validate PDF directory ────────────────────────────────────────────────
    if not os.path.isdir(pdf_folder):
        print(f"\n[ERROR] PDF directory not found: {pdf_folder}")
        print("  Create the folder and place your PDF files inside it.")
        sys.exit(1)

    pdf_files = [
        f for f in os.listdir(pdf_folder)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"\n[WARNING] No PDF files found in: {pdf_folder}")
        print("  Add PDF proposals to that folder and re-run.")
        sys.exit(0)

    print(f"\n  Found {len(pdf_files)} PDF file(s) to process.\n")

    # ── Process each PDF ──────────────────────────────────────────────────────
    results = []
    for idx, filename in enumerate(sorted(pdf_files), start=1):
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"[{idx}/{len(pdf_files)}] Starting: {filename}")
        try:
            summary = process_pdf(pdf_path, collection_name=COLLECTION_NAME)
            results.append(summary)
        except FileNotFoundError as e:
            print(f"  [SKIP] {e}")
        except ConnectionError as e:
            print(f"\n[FATAL] Qdrant is unreachable — stopping pipeline.\n  {e}")
            sys.exit(1)
        except Exception as e:
            print(f"  [ERROR] Failed to process '{filename}': {e}")
            results.append({
                "document": filename,
                "success": False,
                "error": str(e),
            })

    # ── Final run report ──────────────────────────────────────────────────────
    succeeded = [r for r in results if r.get("success")]
    failed    = [r for r in results if not r.get("success")]

    print("=" * 50)
    print("  Run Complete")
    print("=" * 50)
    print(f"  Processed : {len(results)} file(s)")
    print(f"  Succeeded : {len(succeeded)}")
    print(f"  Failed    : {len(failed)}")

    if failed:
        print("\n  Failed files:")
        for r in failed:
            err = r.get("error", "unknown error")
            print(f"    • {r['document']} — {err}")

    print("=" * 50)


if __name__ == "__main__":
    main()
