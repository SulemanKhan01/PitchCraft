"""
state.py — State schema for Proposal Generator LangGraph workflow.
"""

from typing import TypedDict, Optional, List, Dict, Any


class ProposalState(TypedDict):
    """
    State dictionary passed between Proposal Generator nodes.
    """
    messages        : List[Dict[str, str]]     # Input: Chat history from DB
    requirements    : Optional[Dict[str, Any]]  # Step 1: Extracted client requirements
    web_query       : Optional[str]            # Search query built from requirements
    web_context     : Optional[str]            # Step 2: Formatted market context
    web_search_used : Optional[bool]           # Flag if web search provided context
    proposal_content: Optional[str]            # Step 3: Final Markdown proposal text
    error           : Optional[str]            # Error trace (if any)
