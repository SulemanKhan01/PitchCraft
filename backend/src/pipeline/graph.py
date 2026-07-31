"""
graph.py — Assembles and compiles the PDF Ingestion LangGraph workflow.
"""

from langgraph.graph import StateGraph, END
from .state import PDFProcessingState
from .nodes import (
    extract_text_node,
    categorize_node,
    chunk_node,
    embed_node,
    store_vectors_node,
)

builder = StateGraph(PDFProcessingState)

# 1. Register 5 Nodes
builder.add_node("extract_text", extract_text_node)
builder.add_node("categorize", categorize_node)
builder.add_node("chunk", chunk_node)
builder.add_node("embed", embed_node)
builder.add_node("store_vectors", store_vectors_node)

# 2. Define Sequential Flow
builder.set_entry_point("extract_text")
builder.add_edge("extract_text", "categorize")
builder.add_edge("categorize", "chunk")
builder.add_edge("chunk", "embed")
builder.add_edge("embed", "store_vectors")
builder.add_edge("store_vectors", END)

# 3. Compile Graph
pdf_processing_graph = builder.compile()
