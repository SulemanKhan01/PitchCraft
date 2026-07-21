"""
pipeline.py — Orchestrator for the Query Betterment Pipeline.

Chains all 6 processing stages in sequence, handles graceful degradation
at every stage, aggregates confidence, and assembles the final result.

Pipeline execution order:
  Phase 0  ConversationContext   — resolve pronouns / follow-up references
  Stage 1  SpellCorrector        — fix typos, OCR, grammar errors
  Stage 2  IntentDetector        — classify semantic intent (13-class)
  Stage 3  QueryRewriter         — rewrite for retrieval precision
  Stage 4  QueryExpander         — expand vocabulary for recall
  Stage 5  MultiQueryGenerator   — generate semantic variants
  Stage 6  KeywordExtractor      — extract named entities & technical terms

Design principles applied:
  Single Responsibility  — each stage does exactly one thing
  Open / Closed          — add new stage without touching existing ones
  Dependency Injection   — all collaborators injected in __init__
  Graceful Degradation   — any stage failure falls back silently; pipeline continues
"""
from __future__ import annotations

import time
import logging
from typing import Optional

from .models import (
    ConversationTurn,
    ExpansionResult,
    IntentResult,
    IntentType,
    KeywordResult,
    MultiQueryResult,
    QueryBettermentResult,
    DebugTrace,
    StageTrace,
)
from .spell_corrector      import SpellCorrector
from .intent_detector      import IntentDetector
from .query_rewriter       import QueryRewriter
from .query_expander       import QueryExpander
from .multi_query          import MultiQueryGenerator
from .keyword_extractor    import KeywordExtractor
from .conversation_context import ConversationContext
from .confidence           import ConfidenceAggregator, StageConfidence
from .logger               import PipelineLogger
from .utils                import timer

# ─────────────────────────────────────────────────────────────────────────────
# Module logger
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("query_betterment.orchestrator")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [QB:Orchestrator] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


# ─────────────────────────────────────────────────────────────────────────────
# QueryBettermentPipeline
# ─────────────────────────────────────────────────────────────────────────────

class QueryBettermentPipeline:
    """
    Production-Grade Query Betterment Orchestrator.

    Executes a 6-stage enrichment pipeline before the query reaches the
    Embedding Model and Retriever.

    Usage (minimal):
        pipeline = QueryBettermentPipeline()
        result   = pipeline.run("tell me somthing about Edge-Based CV Pipeline")
        refined  = result.final_query   # pass this to retrieve_chunks()

    Usage (with conversation history + debug):
        from src.query_betterment import ConversationTurn
        history = [
            ConversationTurn(role="user",      content="What proposals do we have for AI?"),
            ConversationTurn(role="assistant", content="We have three AI/ML proposals..."),
        ]
        result = pipeline.run(
            query="What about the second one?",
            history=history,
            debug_mode=True,
        )
        print(result.final_query)
        print(result.debug)
    """

    def __init__(self, num_multi_queries: int = 3) -> None:
        """
        Initialise the pipeline and inject all stage collaborators.

        Args:
            num_multi_queries: Number of semantic variants to generate in Stage 5.
                               Clamped to [1, 5].
        """
        self._context_resolver      = ConversationContext()
        self._spell_corrector       = SpellCorrector()
        self._intent_detector       = IntentDetector()
        self._query_rewriter        = QueryRewriter()
        self._query_expander        = QueryExpander()
        self._multi_query           = MultiQueryGenerator(num_queries=num_multi_queries)
        self._keyword_extractor     = KeywordExtractor()
        self._confidence_aggregator = ConfidenceAggregator()
        self._pipeline_logger       = PipelineLogger()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def run(
        self,
        query:      str,
        history:    Optional[list[ConversationTurn]] = None,
        debug_mode: bool = False,
    ) -> QueryBettermentResult:
        """
        Execute the full Query Betterment Pipeline.

        Args:
            query:      Raw user query string (may contain typos, pronouns, etc.)
            history:    Optional conversation history for follow-up resolution.
            debug_mode: If True, populate DebugTrace with per-stage traces.
                        Set False in production to avoid serialisation overhead.

        Returns:
            QueryBettermentResult
              .final_query        → pass to retrieve_chunks() / embedder
              .all_queries        → all semantic variants (future multi-vector use)
              .intent             → detected intent (IntentResult)
              .keywords           → extracted keyword categories (KeywordResult)
              .overall_confidence → aggregated pipeline confidence [0.0, 1.0]
              .debug              → DebugTrace (only when debug_mode=True)
              .total_latency_ms   → end-to-end wall-clock time
        """
        pipeline_start   = time.perf_counter()
        original_query   = query.strip()
        current_query    = original_query

        stage_confidences: list[StageConfidence] = []
        traces:            list[StageTrace]       = []

        # Working variables updated as stages complete
        intent_result:    IntentResult    = IntentResult(
                                                intent=IntentType.SEARCH,
                                                confidence=0.5
                                            )
        expansion_result: ExpansionResult = ExpansionResult(
                                                original=current_query,
                                                expanded_terms=[],
                                                final_query=current_query,
                                                confidence=1.0,
                                            )
        multi_result:     MultiQueryResult = MultiQueryResult(
                                                queries=[current_query],
                                                confidence=1.0,
                                            )
        keyword_result:   KeywordResult   = KeywordResult(confidence=0.5)

        # ── Phase 0: Conversation Context ─────────────────────────────────────
        current_query, conf, trace = self._run_context_resolution(
            current_query, history, debug_mode
        )
        stage_confidences.append(StageConfidence("conversation_context", conf))
        if debug_mode and trace:
            traces.append(trace)

        # ── Stage 1: Spell Correction ─────────────────────────────────────────
        current_query, conf, trace = self._run_spell_correction(
            current_query, debug_mode
        )
        stage_confidences.append(StageConfidence("spell_corrector", conf))
        if debug_mode and trace:
            traces.append(trace)

        # ── Stage 2: Intent Detection ─────────────────────────────────────────
        intent_result, trace = self._run_intent_detection(current_query, debug_mode)
        stage_confidences.append(StageConfidence("intent_detector", intent_result.confidence))
        if debug_mode and trace:
            traces.append(trace)

        # ── Stage 3: Query Rewriting ──────────────────────────────────────────
        current_query, conf, trace = self._run_query_rewriting(
            current_query, intent_result.intent, debug_mode
        )
        stage_confidences.append(StageConfidence("query_rewriter", conf))
        if debug_mode and trace:
            traces.append(trace)

        # ── Stage 4: Query Expansion ──────────────────────────────────────────
        expansion_result, trace = self._run_query_expansion(
            current_query, intent_result.intent, debug_mode
        )
        stage_confidences.append(
            StageConfidence("query_expander", expansion_result.confidence)
        )
        if debug_mode and trace:
            traces.append(trace)

        # Use the expanded query as the base for the remaining stages
        expanded_query = expansion_result.final_query

        # ── Stage 5: Multi-Query Generation ──────────────────────────────────
        multi_result, trace = self._run_multi_query(
            expanded_query, intent_result.intent, debug_mode
        )
        stage_confidences.append(StageConfidence("multi_query", multi_result.confidence))
        if debug_mode and trace:
            traces.append(trace)

        # ── Stage 6: Keyword Extraction ───────────────────────────────────────
        keyword_result, trace = self._run_keyword_extraction(expanded_query, debug_mode)
        stage_confidences.append(
            StageConfidence("keyword_extractor", keyword_result.confidence)
        )
        if debug_mode and trace:
            traces.append(trace)

        # ── Assemble Final Query ──────────────────────────────────────────────
        final_query = self._assemble_final_query(expanded_query, keyword_result)

        # Deduplicate: final_query first, then multi-query variants
        all_queries = list(
            dict.fromkeys([final_query] + multi_result.queries)
        )

        # ── Confidence + Timing ───────────────────────────────────────────────
        overall_confidence = self._confidence_aggregator.aggregate(stage_confidences)
        total_latency_ms   = (time.perf_counter() - pipeline_start) * 1_000

        # ── Pipeline-level Log ────────────────────────────────────────────────
        self._pipeline_logger.log_pipeline(
            original=original_query,
            final=final_query,
            total_latency_ms=total_latency_ms,
            overall_confidence=overall_confidence,
        )

        return QueryBettermentResult(
            original_query=original_query,
            final_query=final_query,
            all_queries=all_queries,
            intent=intent_result,
            keywords=keyword_result,
            overall_confidence=overall_confidence,
            debug=DebugTrace(traces=traces) if debug_mode else None,
            total_latency_ms=round(total_latency_ms, 2),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Private Stage Runners
    # Each runner:  executes stage → logs → builds optional trace → returns
    # Graceful degradation: any exception is caught; fallback values returned
    # ─────────────────────────────────────────────────────────────────────────

    def _run_context_resolution(
        self,
        query:      str,
        history:    Optional[list[ConversationTurn]],
        debug_mode: bool,
    ) -> tuple[str, float, Optional[StageTrace]]:
        with timer() as t:
            try:
                resolved, conf = self._context_resolver.resolve(query, history)
            except Exception as exc:
                self._pipeline_logger.log_error("conversation_context", exc)
                resolved, conf = query, 1.0

        self._pipeline_logger.log_stage(
            "conversation_context", query, resolved, t["elapsed_ms"], conf
        )
        trace = self._make_trace(
            "conversation_context", query, resolved, t["elapsed_ms"], conf, debug_mode
        )
        return resolved, conf, trace

    def _run_spell_correction(
        self, query: str, debug_mode: bool
    ) -> tuple[str, float, Optional[StageTrace]]:
        with timer() as t:
            try:
                result    = self._spell_corrector.correct(query)
                corrected = result.corrected
                conf      = result.confidence
            except Exception as exc:
                self._pipeline_logger.log_error("spell_corrector", exc)
                corrected, conf = query, 1.0

        self._pipeline_logger.log_stage(
            "spell_corrector", query, corrected, t["elapsed_ms"], conf
        )
        trace = self._make_trace(
            "spell_corrector", query, corrected, t["elapsed_ms"], conf, debug_mode
        )
        return corrected, conf, trace

    def _run_intent_detection(
        self, query: str, debug_mode: bool
    ) -> tuple[IntentResult, Optional[StageTrace]]:
        with timer() as t:
            try:
                result = self._intent_detector.detect(query)
            except Exception as exc:
                self._pipeline_logger.log_error("intent_detector", exc)
                result = IntentResult(intent=IntentType.SEARCH, confidence=0.5)

        self._pipeline_logger.log_stage(
            "intent_detector", query, result.intent.value,
            t["elapsed_ms"], result.confidence,
        )
        trace = self._make_trace(
            "intent_detector", query, result.intent.value,
            t["elapsed_ms"], result.confidence, debug_mode,
        )
        return result, trace

    def _run_query_rewriting(
        self, query: str, intent: IntentType, debug_mode: bool
    ) -> tuple[str, float, Optional[StageTrace]]:
        with timer() as t:
            try:
                result    = self._query_rewriter.rewrite(query, intent)
                rewritten = result.rewritten
                conf      = result.confidence
            except Exception as exc:
                self._pipeline_logger.log_error("query_rewriter", exc)
                rewritten, conf = query, 0.7

        self._pipeline_logger.log_stage(
            "query_rewriter", query, rewritten, t["elapsed_ms"], conf
        )
        trace = self._make_trace(
            "query_rewriter", query, rewritten, t["elapsed_ms"], conf, debug_mode
        )
        return rewritten, conf, trace

    def _run_query_expansion(
        self, query: str, intent: IntentType, debug_mode: bool
    ) -> tuple[ExpansionResult, Optional[StageTrace]]:
        with timer() as t:
            try:
                result = self._query_expander.expand(query, intent)
            except Exception as exc:
                self._pipeline_logger.log_error("query_expander", exc)
                result = ExpansionResult(
                    original=query,
                    expanded_terms=[],
                    final_query=query,
                    confidence=0.7,
                )

        self._pipeline_logger.log_stage(
            "query_expander", query, result.final_query,
            t["elapsed_ms"], result.confidence,
        )
        trace = self._make_trace(
            "query_expander", query, result.final_query,
            t["elapsed_ms"], result.confidence, debug_mode,
        )
        return result, trace

    def _run_multi_query(
        self, query: str, intent: IntentType, debug_mode: bool
    ) -> tuple[MultiQueryResult, Optional[StageTrace]]:
        with timer() as t:
            try:
                result = self._multi_query.generate(query, intent)
            except Exception as exc:
                self._pipeline_logger.log_error("multi_query", exc)
                result = MultiQueryResult(queries=[query], confidence=0.5)

        self._pipeline_logger.log_stage(
            "multi_query", query, str(result.queries),
            t["elapsed_ms"], result.confidence,
        )
        trace = self._make_trace(
            "multi_query", query, str(result.queries),
            t["elapsed_ms"], result.confidence, debug_mode,
        )
        return result, trace

    def _run_keyword_extraction(
        self, query: str, debug_mode: bool
    ) -> tuple[KeywordResult, Optional[StageTrace]]:
        with timer() as t:
            try:
                result = self._keyword_extractor.extract(query)
            except Exception as exc:
                self._pipeline_logger.log_error("keyword_extractor", exc)
                result = KeywordResult(confidence=0.5)

        kw_summary = str(result.all_keywords())
        self._pipeline_logger.log_stage(
            "keyword_extractor", query, kw_summary,
            t["elapsed_ms"], result.confidence,
        )
        trace = self._make_trace(
            "keyword_extractor", query, kw_summary,
            t["elapsed_ms"], result.confidence, debug_mode,
        )
        return result, trace

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _assemble_final_query(expanded_query: str, keyword_result: KeywordResult) -> str:
        """
        Produce the richest single-string query to send to the embedding model.

        Strategy: append any extracted keyword terms that are NOT already
        present in the expanded query (case-insensitive deduplication).

        This ensures the embedding captures both the full semantic context
        from expansion (Stage 4) AND the exact technical identifiers from
        NER (Stage 6).
        """
        all_kws = keyword_result.all_keywords()
        if not all_kws:
            return expanded_query

        lower_expanded = expanded_query.lower()
        new_terms = [
            kw for kw in all_kws
            if kw.lower() not in lower_expanded
        ]

        if not new_terms:
            return expanded_query

        return f"{expanded_query} {' '.join(new_terms)}"

    @staticmethod
    def _make_trace(
        stage:      str,
        inp:        str,
        out:        str,
        latency_ms: float,
        confidence: float,
        debug_mode: bool,
        error:      Optional[str] = None,
    ) -> Optional[StageTrace]:
        """Build a StageTrace only when debug_mode is active (zero overhead otherwise)."""
        if not debug_mode:
            return None
        return StageTrace(
            stage=stage,
            input=inp[:500],
            output=out[:500],
            latency_ms=round(latency_ms, 2),
            confidence=round(confidence, 4),
            error=error,
        )


if __name__ == "__main__":
    import os
    import sys
    
    # Ensure project root is in sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    print("Running Query Betterment Pipeline Demo/Test...")
    pipeline = QueryBettermentPipeline(num_multi_queries=2)
    
    test_query = "tell me somthing about Edge-Basd Computr Vision (CV) Pipline"
    print(f"Original Query: '{test_query}'\n")
    
    result = pipeline.run(query=test_query, debug_mode=True)
    
    print("=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print("Final Query:", result.final_query)
    print("Detected Intent:", result.intent.intent.value if result.intent else "None")
    print("Extracted Keywords:", result.keywords.all_keywords() if result.keywords else [])
    print("Confidence:", round(result.overall_confidence, 3))
    print("Total Latency:", round(result.total_latency_ms, 2), "ms")
    print("=" * 60)
