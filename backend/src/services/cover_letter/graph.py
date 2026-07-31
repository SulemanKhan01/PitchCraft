"""
graph.py — Assembles and compiles the Cover Letter LangGraph workflow.
"""

from langgraph.graph import StateGraph, END
from .state import CoverLetterState
from .nodes import parse_jd_node, retrieve_chunks_node, generate_content_node

# 1. Instantiate Graph with State Schema
builder = StateGraph(CoverLetterState)

# 2. Register Nodes
builder.add_node("parse_jd", parse_jd_node)
builder.add_node("retrieve_chunks", retrieve_chunks_node)
builder.add_node("generate_content", generate_content_node)

# 3. Define Flow Edges
builder.set_entry_point("parse_jd")
builder.add_edge("parse_jd", "retrieve_chunks")
builder.add_edge("retrieve_chunks", "generate_content")
builder.add_edge("generate_content", END)

# 4. Compile Graph
cover_letter_graph = builder.compile()
