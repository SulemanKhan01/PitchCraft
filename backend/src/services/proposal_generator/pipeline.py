"""
pipeline.py — Public LangGraph entrypoint wrapper for Proposal Generator.
"""

import logging
from .state import ProposalState
from .graph import proposal_graph

logger = logging.getLogger("proposal_generator.pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [Proposal:Pipeline] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def generate_proposal(messages: list[dict]) -> dict:
    """
    Main entrypoint called by FastAPI proposal generation endpoint.
    Orchestrates execution via LangGraph.
    """
    logger.info("=== LangGraph Proposal Generation Pipeline Started ===")

    initial_state: ProposalState = {
        "messages": messages,
        "requirements": None,
        "web_query": None,
        "web_context": None,
        "web_search_used": False,
        "proposal_content": None,
        "error": None,
    }

    # Execute compiled LangGraph graph
    final_state = proposal_graph.invoke(initial_state)

    logger.info("=== LangGraph Proposal Generation Pipeline Completed ===")

    return {
        "proposal_content": final_state.get("proposal_content", ""),
        "requirements": final_state.get("requirements") or {},
        "web_search_used": final_state.get("web_search_used", False),
    }


# Standalone CLI test
if __name__ == "__main__":
    sample_messages = [
        {"role": "user", "content": "We want to build a mobile e-commerce application with React Native and Stripe."},
        {"role": "assistant", "content": "Great, what is your estimated timeline and budget?"},
        {"role": "user", "content": "Budget is $25k and timeline is 2 months."},
    ]
    result = generate_proposal(sample_messages)
    print("\n===== PROPOSAL RESULT =====")
    print(f"Web Search Used: {result['web_search_used']}")
    print(f"Content        : {result['proposal_content'][:200]}...")
