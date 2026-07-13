"""
models.py — All Pydantic data contracts for the Query Betterment Pipeline.

Zero business logic lives here.
Every stage input and output is typed through these models.
"""
from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class IntentType(str, enum.Enum):
    """13-class intent taxonomy for query classification."""
    QUESTION       = "question"
    SEARCH         = "search"
    COMPARISON     = "comparison"
    DEFINITION     = "definition"
    SUMMARIZATION  = "summarization"
    DEBUGGING      = "debugging"
    PROGRAMMING    = "programming"
    DOCUMENTATION  = "documentation"
    HOW_TO         = "how_to"
    CONVERSATION   = "conversation"
    FOLLOW_UP      = "follow_up"
    CLASSIFICATION = "classification"
    UNKNOWN        = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Conversation
# ─────────────────────────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    """A single turn in a conversation history."""
    role: str    = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Raw message content")


# ─────────────────────────────────────────────────────────────────────────────
# Stage Result Models
# ─────────────────────────────────────────────────────────────────────────────

class SpellCorrectionResult(BaseModel):
    """Output of Stage 1 — SpellCorrector."""
    original:  str
    corrected: str
    changes:   list[str]  = Field(default_factory=list,
                                  description="Human-readable list of corrections made")
    confidence: float     = Field(ge=0.0, le=1.0)


class IntentResult(BaseModel):
    """Output of Stage 2 — IntentDetector."""
    intent:     IntentType
    sub_intent: Optional[str] = Field(
        default=None,
        description="Optional fine-grained qualifier, e.g. 'runtime error'"
    )
    confidence: float = Field(ge=0.0, le=1.0)


class RewriteResult(BaseModel):
    """Output of Stage 3 — QueryRewriter."""
    original:  str
    rewritten: str
    rationale: str  = Field(default="",
                            description="One-sentence explanation of rewriting decisions")
    confidence: float = Field(ge=0.0, le=1.0)


class ExpansionResult(BaseModel):
    """Output of Stage 4 — QueryExpander."""
    original:       str
    expanded_terms: list[str] = Field(default_factory=list,
                                      description="Synonyms, aliases, and related terms added")
    final_query:    str       = Field(description="Original query with expansions appended")
    confidence:     float     = Field(ge=0.0, le=1.0)


class MultiQueryResult(BaseModel):
    """Output of Stage 5 — MultiQueryGenerator."""
    queries:    list[str] = Field(default_factory=list,
                                  description="Semantically distinct query variants")
    confidence: float     = Field(ge=0.0, le=1.0)


class KeywordResult(BaseModel):
    """Output of Stage 6 — KeywordExtractor."""
    entities:   list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    languages:  list[str] = Field(default_factory=list)
    errors:     list[str] = Field(default_factory=list)
    tools:      list[str] = Field(default_factory=list)
    models:     list[str] = Field(default_factory=list)
    file_names: list[str] = Field(default_factory=list)
    versions:   list[str] = Field(default_factory=list)
    keywords:   list[str] = Field(default_factory=list)
    confidence: float     = Field(ge=0.0, le=1.0, default=0.5)

    def all_keywords(self) -> list[str]:
        """
        Return a deduplicated, flat list of every extracted term.
        Preserves insertion order; de-duplicates case-insensitively.
        """
        seen: set[str] = set()
        result: list[str] = []
        for term in (
            self.entities + self.frameworks + self.languages +
            self.errors   + self.tools      + self.models    +
            self.file_names + self.versions + self.keywords
        ):
            key = term.strip().lower()
            if key and key not in seen:
                seen.add(key)
                result.append(term.strip())
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Debug / Tracing
# ─────────────────────────────────────────────────────────────────────────────

class StageTrace(BaseModel):
    """Per-stage execution record — only populated when debug_mode=True."""
    stage:      str
    input:      str
    output:     str
    latency_ms: float
    confidence: float
    error:      Optional[str] = None


class DebugTrace(BaseModel):
    """Aggregated debug trace for the full pipeline run."""
    traces: list[StageTrace] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Output
# ─────────────────────────────────────────────────────────────────────────────

class QueryBettermentResult(BaseModel):
    """
    Final output of QueryBettermentPipeline.run().

    The caller passes ``final_query`` directly to the Embedding Model /
    Retriever.  ``all_queries`` is available for future multi-vector retrieval.
    """
    original_query:     str
    final_query:        str            = Field(description="Enriched query ready for the embedder")
    all_queries:        list[str]      = Field(default_factory=list,
                                               description="Semantic variants for multi-vector retrieval")
    intent:             Optional[IntentResult]  = None
    keywords:           Optional[KeywordResult] = None
    overall_confidence: float          = Field(ge=0.0, le=1.0, default=1.0)
    debug:              Optional[DebugTrace] = Field(
                            default=None,
                            description="Full stage traces — only set when debug_mode=True"
                        )
    total_latency_ms:   float = 0.0
