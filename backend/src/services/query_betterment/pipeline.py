"""
pipeline.py — Streamlined Orchestrator for the Query Betterment Pipeline.

Executes a fast 2-step process:
  Phase 0  ConversationContext — Resolves pronouns & follow-ups using chat history (if present)
  Phase 1  UnifiedQueryEnricher — Performs typo fix, intent detection, keyword extraction, and rewriting in 1 LLM call
"""
from __future__ import annotations

import time
import logging
from typing import Optional

from .models import (
    ConversationTurn,
    IntentResult,
    IntentType,
    KeywordResult,
    QueryBettermentResult,
    DebugTrace,
    StageTrace,
)
from .conversation_context import ConversationContext
from .unified_enricher import UnifiedQueryEnricher
from .logger import PipelineLogger

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


class QueryBettermentPipeline:
    """
    Streamlined Production Query Betterment Orchestrator.
    Reduces 7 separate LLM calls down to 1–2 fast calls.
    """

    def __init__(self, num_multi_queries: int = 3) -> None:
        self._context_resolver = ConversationContext()
        self._unified_enricher = UnifiedQueryEnricher()
        self._pipeline_logger = PipelineLogger()

    def run(
        self,
        query: str,
        history: Optional[list[ConversationTurn]] = None,
        debug_mode: bool = False,
    ) -> QueryBettermentResult:
        """
        Execute the streamlined Query Betterment Pipeline.
        """
        pipeline_start = time.perf_counter()
        original_query = query.strip()
        current_query = original_query
        traces: list[StageTrace] = []

        # ── Phase 0: Conversation Context (Only if history exists) ────────────
        if history:
            current_query, conf, trace = self._run_context_resolution(current_query, history, debug_mode)
            if debug_mode and trace:
                traces.append(trace)

        # ── Phase 1: Unified Enrichment (Single Master LLM Call) ──────────────
        enrich_start = time.perf_counter()
        enrich_res = self._unified_enricher.enrich(current_query)
        enrich_latency = (time.perf_counter() - enrich_start) * 1000

        final_query = enrich_res.get("final_query", current_query)
        raw_intent = enrich_res.get("intent", "search")
        keywords_list = enrich_res.get("keywords", [])
        overall_confidence = enrich_res.get("confidence", 0.9)

        # Build model contracts for downstream callers
        try:
            intent_enum = IntentType(raw_intent)
        except ValueError:
            intent_enum = IntentType.SEARCH

        intent_result = IntentResult(intent=intent_enum, confidence=overall_confidence)
        keyword_result = KeywordResult(keywords=keywords_list, confidence=overall_confidence)

        if debug_mode:
            traces.append(StageTrace(
                stage="unified_enricher",
                input=current_query,
                output=final_query,
                latency_ms=round(enrich_latency, 2),
                confidence=round(overall_confidence, 4),
            ))

        total_latency_ms = (time.perf_counter() - pipeline_start) * 1000

        self._pipeline_logger.log_pipeline(
            original=original_query,
            final=final_query,
            total_latency_ms=total_latency_ms,
            overall_confidence=overall_confidence,
        )

        return QueryBettermentResult(
            original_query=original_query,
            final_query=final_query,
            all_queries=[final_query],
            intent=intent_result,
            keywords=keyword_result,
            overall_confidence=overall_confidence,
            debug=DebugTrace(traces=traces) if debug_mode else None,
            total_latency_ms=round(total_latency_ms, 2),
        )

    def _run_context_resolution(
        self,
        query: str,
        history: Optional[list[ConversationTurn]],
        debug_mode: bool,
    ) -> tuple[str, float, Optional[StageTrace]]:
        start = time.perf_counter()
        try:
            resolved, conf = self._context_resolver.resolve(query, history)
        except Exception as exc:
            self._pipeline_logger.log_error("conversation_context", exc)
            resolved, conf = query, 1.0

        latency_ms = (time.perf_counter() - start) * 1000
        trace = None
        if debug_mode:
            trace = StageTrace(
                stage="conversation_context",
                input=query,
                output=resolved,
                latency_ms=round(latency_ms, 2),
                confidence=round(conf, 4),
            )
        return resolved, conf, trace
