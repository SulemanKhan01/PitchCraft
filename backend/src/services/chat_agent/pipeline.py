"""
pipeline.py — Public entrypoint wrapper for RAG Chat Agent.
"""

import logging
from typing import Optional, List, Dict, Any
from .state import ChatAgentState
from .graph import chat_agent_graph

logger = logging.getLogger("chat_agent.pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [ChatAgent:Pipeline] %(levelname)s — %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
    logger.propagate = False


def run_chat_agent(
    question: str,
    previous_interaction_id: Optional[str] = None,
    history: Optional[List[Any]] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Main entrypoint called by FastAPI chat router (/api/chat/chat).
    Orchestrates execution via LangGraph.
    """
    logger.info("=== LangGraph Chat Agent Started ===")

    initial_state: ChatAgentState = {
        "question": question,
        "previous_interaction_id": previous_interaction_id,
        "history": history,
        "debug_mode": debug,
        "qb_result": None,
        "raw_chunks": [],
        "chunks": [],
        "web_context": "",
        "use_web_search": False,
        "answer_text": "",
        "interaction_id": None,
        "source": "unknown",
        "error": None,
    }

    final_state = chat_agent_graph.invoke(initial_state)

    logger.info(f"=== LangGraph Chat Agent Completed (Source: {final_state.get('source')}) ===")

    result = {
        "answer": final_state.get("answer_text", ""),
        "interaction_id": final_state.get("interaction_id"),
        "source": final_state.get("source"),
    }

    if debug and final_state.get("qb_result"):
        qb_result = final_state["qb_result"]
        result["query_betterment"] = {
            "original_query": qb_result.original_query,
            "final_query": qb_result.final_query,
            "all_queries": qb_result.all_queries,
            "intent": qb_result.intent.model_dump() if qb_result.intent else None,
            "keywords": qb_result.keywords.model_dump() if qb_result.keywords else None,
            "overall_confidence": qb_result.overall_confidence,
            "total_latency_ms": qb_result.total_latency_ms,
            "stages": [t.model_dump() for t in qb_result.debug.traces] if qb_result.debug else [],
        }

    return result


if __name__ == "__main__":
    res = run_chat_agent("What projects have you built?")
    print("\n===== CHAT AGENT RESULT =====")
    print(res)
