"""
state.py — State schema for PDF Ingestion LangGraph workflow.
"""

from typing import TypedDict, Optional, List, Dict, Any


class PDFProcessingState(TypedDict):
    """
    State dictionary passed between PDF processing nodes.
    """
    pdf_path       : str                          # Input: Absolute/relative path to PDF
    collection_name: str                          # Input: Qdrant collection name
    extracted_text : Optional[str]                # Node 1: Extracted raw text
    category       : Optional[str]                # Node 2: Category string
    chunks         : Optional[List[Dict[str, Any]]]# Node 3: Generated text chunks
    embeddings     : Optional[List[Dict[str, Any]]]# Node 4: Embedded chunk vectors
    stored         : Optional[int]                # Node 5: Number of vectors saved in Qdrant
    success        : Optional[bool]               # Pipeline status
    error          : Optional[str]                # Error message (if any)
