"""
confidence.py — Weighted confidence aggregation across all pipeline stages.

Responsibility:
  - Accept per-stage confidence scores
  - Apply per-stage weights (tunable without code changes)
  - Return a single overall confidence in [0.0, 1.0]

Design: Open/Closed — add new stages to DEFAULT_WEIGHTS dict; no logic changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# Data Container
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StageConfidence:
    """Holds the name and confidence score for a single pipeline stage."""
    stage_name: str
    confidence: float
    weight:     float = field(default=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Aggregator
# ─────────────────────────────────────────────────────────────────────────────

class ConfidenceAggregator:
    """
    Computes a weighted average confidence score from all pipeline stages.

    Weights reflect each stage's relative impact on final query quality:
      - query_rewriter has the highest weight (most transformative stage)
      - intent_detector is the second highest (informs all downstream stages)
      - multi_query and conversation_context are lower (auxiliary stages)

    Weights are read from DEFAULT_WEIGHTS at runtime — no code change needed
    to tune them; override by subclassing or passing a custom weights dict.
    """

    DEFAULT_WEIGHTS: dict[str, float] = {
        "conversation_context": 0.8,
        "spell_corrector":      1.0,
        "intent_detector":      1.2,
        "query_rewriter":       1.5,
        "query_expander":       1.0,
        "multi_query":          0.8,
        "keyword_extractor":    1.0,
    }

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        """
        Args:
            weights: Optional custom weight mapping. Falls back to DEFAULT_WEIGHTS
                     for any stage not present in the provided dict.
        """
        self._weights: dict[str, float] = weights or self.DEFAULT_WEIGHTS

    def aggregate(self, stage_confidences: list[StageConfidence]) -> float:
        """
        Compute the weighted average confidence across all stages.

        Args:
            stage_confidences: List of StageConfidence records from the pipeline.

        Returns:
            A float in [0.0, 1.0]. Returns 1.0 if the list is empty.
        """
        if not stage_confidences:
            return 1.0

        total_weight  = 0.0
        weighted_sum  = 0.0

        for sc in stage_confidences:
            w = self._weights.get(sc.stage_name, 1.0)
            weighted_sum  += sc.confidence * w
            total_weight  += w

        if total_weight == 0.0:
            return 1.0

        raw = weighted_sum / total_weight
        return max(0.0, min(1.0, raw))
