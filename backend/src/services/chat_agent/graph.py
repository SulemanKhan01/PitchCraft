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


def route_after_query_betterment(state: ChatAgentState) -> str:
    """
    Conditional Edge Function:
    If input validation rejected the query, skip all remaining nodes.
    Otherwise, continue to retrieval.
    """
    if state.get("source") == "input_validation_rejected":
        return "end"
    return "retrieve_context"


builder = StateGraph(ChatAgentState)

# 1. Add 4 Nodes
builder.add_node("query_betterment", query_betterment_node)
builder.add_node("retrieve_context", retrieve_context_node)
builder.add_node("web_search_fallback", web_search_fallback_node)
builder.add_node("generate_answer", generate_answer_node)

# 2. Entry point
builder.set_entry_point("query_betterment")

# 3. CONDITIONAL EDGE after query_betterment (short-circuit on validation rejection)
builder.add_conditional_edges(
    "query_betterment",
    route_after_query_betterment,
    {
        "retrieve_context": "retrieve_context",
        "end": END,
    }
)

# 4. CONDITIONAL EDGE after retrieval
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
