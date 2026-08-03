"""
state.py — State schema for RAG Chat Agent LangGraph workflow.
"""

from typing import TypedDict, Optional, List, Dict, Any


class ChatAgentState(TypedDict):
    """
    State dictionary passed between Chat Agent nodes.
    """
    question               : str                         # Input: User's prompt
    previous_interaction_id: Optional[str]               # Input: Gemini interaction context
    history                : Optional[List[Any]]         # Input: Conversation turns history
    debug_mode             : Optional[bool]              # Input: Debug flag

    # Internal Node Outputs
    qb_result              : Optional[Any]               # Step 1: Betterment output
    raw_chunks             : Optional[List[Dict[str, Any]]]# Step 2: Unfiltered Qdrant chunks
    chunks                 : Optional[List[Dict[str, Any]]]# Step 2: High-confidence chunks (score >= 0.60)
    web_context            : Optional[str]               # Step 3 (Fallback): Tavily web search results
    use_web_search         : Optional[bool]              # Flag if web search was triggered
    answer_text            : Optional[str]               # Step 4: Final LLM answer
    interaction_id         : Optional[str]               # Gemini interaction ID
    source                 : Optional[str]               # "rag", "web_search", or "gemini_knowledge"
    error                  : Optional[str]               # Error trace (if any)
