"""
__init__.py — Public API surface for the Query Betterment module.

Only the symbols listed in __all__ form the public contract.
All internal implementation details remain private to the package.

Typical usage:

    from src.query_betterment import QueryBettermentPipeline, ConversationTurn

    pipeline = QueryBettermentPipeline()

    # Minimal (no history, no debug)
    result = pipeline.run("tell me somthing about Edge-Based CV pipeline")
    refined_query = result.final_query   # → pass to retrieve_chunks()

    # With conversation history
    history = [
        ConversationTurn(role="user",      content="What AI proposals do we have?"),
        ConversationTurn(role="assistant", content="We have three AI/ML proposals..."),
    ]
    result = pipeline.run("What about the second one?", history=history)

    # With full debug trace
    result = pipeline.run("my query", debug_mode=True)
    for trace in result.debug.traces:
        print(trace.stage, trace.latency_ms, trace.confidence)
"""

from .pipeline import QueryBettermentPipeline
from .models   import (
    QueryBettermentResult,
    ConversationTurn,
    IntentType,
    IntentResult,
    KeywordResult,
    SpellCorrectionResult,
    RewriteResult,
    ExpansionResult,
    MultiQueryResult,
    DebugTrace,
    StageTrace,
)

__all__: list[str] = [
    # Primary interface
    "QueryBettermentPipeline",
    "QueryBettermentResult",

    # Conversation
    "ConversationTurn",

    # Enumerations
    "IntentType",

    # Stage result models (useful for type-annotating callers)
    "IntentResult",
    "KeywordResult",
    "SpellCorrectionResult",
    "RewriteResult",
    "ExpansionResult",
    "MultiQueryResult",

    # Debug / tracing
    "DebugTrace",
    "StageTrace",
]
