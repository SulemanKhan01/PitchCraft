"""
graph.py — Assembles and compiles the Proposal Generator LangGraph workflow.
"""

from langgraph.graph import StateGraph, END
from .state import ProposalState
from .nodes import analyze_chat_node, web_search_node, write_proposal_node

builder = StateGraph(ProposalState)

builder.add_node("analyze_chat", analyze_chat_node)
builder.add_node("web_search", web_search_node)
builder.add_node("write_proposal", write_proposal_node)

builder.set_entry_point("analyze_chat")
builder.add_edge("analyze_chat", "web_search")
builder.add_edge("web_search", "write_proposal")
builder.add_edge("write_proposal", END)

proposal_graph = builder.compile()
