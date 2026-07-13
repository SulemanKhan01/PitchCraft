"""
logger.py — Structured, per-stage pipeline logger for the Query Betterment module.

Every stage logs:
  - Stage name
  - Input text (truncated for readability)
  - Output text (truncated for readability)
  - Execution latency in milliseconds
  - Confidence score
  - Error details (if any)

All output is emitted as JSON-serializable log records for easy parsing
by log aggregation tools (e.g., ELK, Datadog, Cloud Logging).
"""
from __future__ import annotations

import json
import logging
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_logger(name: str) -> logging.Logger:
    """Build and configure a named logger under the 'query_betterment' namespace."""
    logger = logging.getLogger(f"query_betterment.{name}")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [QB:%(name)s] %(levelname)s — %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


_TRUNCATE_LEN: int = 300  # max chars for input/output in log records


# ─────────────────────────────────────────────────────────────────────────────
# Public Logger Class
# ─────────────────────────────────────────────────────────────────────────────

class PipelineLogger:
    """
    Centralized structured logger for the Query Betterment Pipeline.

    Injected into the orchestrator (pipeline.py) and used for every stage.
    Serializes records as JSON for compatibility with log aggregation systems.
    """

    def __init__(self) -> None:
        self._log = _make_logger("pipeline")

    # ── Stage-level ──────────────────────────────────────────────────────────

    def log_stage(
        self,
        stage_name:  str,
        input_text:  str,
        output_text: str,
        latency_ms:  float,
        confidence:  float,
        error:       Optional[str] = None,
    ) -> None:
        """
        Emit a structured log record for a completed pipeline stage.

        Args:
            stage_name:  Identifier of the stage (e.g. 'spell_corrector').
            input_text:  Raw input passed to the stage.
            output_text: Output produced by the stage.
            latency_ms:  Wall-clock execution time in milliseconds.
            confidence:  Stage confidence score in [0.0, 1.0].
            error:       Error message if the stage failed, else None.
        """
        level = logging.ERROR if error else logging.INFO
        payload: dict = {
            "stage":      stage_name,
            "input":      input_text[:_TRUNCATE_LEN],
            "output":     output_text[:_TRUNCATE_LEN],
            "latency_ms": round(latency_ms, 2),
            "confidence": round(confidence, 4),
        }
        if error:
            payload["error"] = error
        self._log.log(level, json.dumps(payload))

    # ── Pipeline-level ───────────────────────────────────────────────────────

    def log_pipeline(
        self,
        original:           str,
        final:              str,
        total_latency_ms:   float,
        overall_confidence: float,
    ) -> None:
        """
        Emit a summary record for the full pipeline run.

        Args:
            original:           Raw user query before any processing.
            final:              Enriched query after all stages.
            total_latency_ms:   End-to-end wall-clock time in milliseconds.
            overall_confidence: Aggregated confidence across all stages.
        """
        self._log.info(
            json.dumps({
                "event":              "pipeline_complete",
                "original_query":     original[:_TRUNCATE_LEN],
                "final_query":        final[:_TRUNCATE_LEN],
                "total_latency_ms":   round(total_latency_ms, 2),
                "overall_confidence": round(overall_confidence, 4),
            })
        )

    # ── Error-level ──────────────────────────────────────────────────────────

    def log_error(self, stage_name: str, error: Exception) -> None:
        """
        Emit an error record when a stage raises an unexpected exception.

        Args:
            stage_name: Identifier of the failing stage.
            error:      The caught exception.
        """
        self._log.error(
            json.dumps({
                "stage":         stage_name,
                "error_type":    type(error).__name__,
                "error_message": str(error),
            })
        )
