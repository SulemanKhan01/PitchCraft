"""
graph.py — Assembles RAG Chat Agent LangGraph workflow with Conditional Routing.
"""

from langgraph.graph import StateGraph, END
from .state import ChatAgentState
from .nodes import (
    query_betterment_node,
    retrieve_context_node,
    web_search_fallback_node,
    generate_answer_node,
)


def route_after_retrieval(state: ChatAgentState) -> str:
    """
    Conditional Edge Function:
    If Qdrant returned valid chunks (score >= 0.60), route directly to LLM answer generation.
    Otherwise, route to Web Search fallback node first.
    """
    chunks = state.get("chunks") or []
    if chunks:
        return "generate_answer"
    else:
        return "web_search_fallback"


builder = StateGraph(ChatAgentState)

# 1. Add 4 Nodes
builder.add_node("query_betterment", query_betterment_node)
builder.add_node("retrieve_context", retrieve_context_node)
builder.add_node("web_search_fallback", web_search_fallback_node)
builder.add_node("generate_answer", generate_answer_node)

# 2. Add Fixed Edges
builder.set_entry_point("query_betterment")
builder.add_edge("query_betterment", "retrieve_context")

# 3. Add CONDITIONAL EDGE (Dynamic Router)
builder.add_conditional_edges(
    "retrieve_context",
    route_after_retrieval,
    {
        "generate_answer": "generate_answer",
        "web_search_fallback": "web_search_fallback",
    }
)

builder.add_edge("web_search_fallback", "generate_answer")
builder.add_edge("generate_answer", END)

# 4. Compile Graph
chat_agent_graph = builder.compile()
