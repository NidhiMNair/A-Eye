"""
track2/pipeline.py
====================
Main Track 2 processing pipeline orchestrator.

Executes the end-to-end Track 2 flow:
  FrameBatch
      ↓
  VLM (GeminiVLM or MockVLM)
      ↓
  PerceptionResult
      ↓
  Spatial Reasoning (image-space)
      ↓
  Context Reasoning (temporal & persistence)
      ↓
  Priority / Risk Assessment
      ↓
  Assistance Decision
      ↓
  Track2Result
"""

from __future__ import annotations

from typing import Optional

from track2.context import ContextReasoner
from track2.decision import AssistanceDecisionEngine
from track2.models import (
    FrameBatch,
    Track2Result,
)
from track2.spatial import SpatialReasoner
from track2.vlm import MockVLM, VisionLanguageModel


class Track2Pipeline:
    """
    Orchestrates the Track 2 reasoning pipeline from camera frames to structured assistance.
    """

    def __init__(
        self,
        vlm: Optional[VisionLanguageModel] = None,
        spatial_reasoner: Optional[SpatialReasoner] = None,
        context_reasoner: Optional[ContextReasoner] = None,
        decision_engine: Optional[AssistanceDecisionEngine] = None,
    ) -> None:
        """
        Initialize the Track 2 pipeline.

        Args:
            vlm: VisionLanguageModel instance (defaults to MockVLM for offline execution).
            spatial_reasoner: Optional custom SpatialReasoner.
            context_reasoner: Optional custom ContextReasoner.
            decision_engine: Optional custom AssistanceDecisionEngine.
        """
        self._vlm = vlm if vlm is not None else MockVLM()
        self._spatial = spatial_reasoner if spatial_reasoner is not None else SpatialReasoner()
        self._context = context_reasoner if context_reasoner is not None else ContextReasoner()
        self._decision = decision_engine if decision_engine is not None else AssistanceDecisionEngine()

    @property
    def vlm(self) -> VisionLanguageModel:
        """The active Vision-Language Model."""
        return self._vlm

    def reset_context(self) -> None:
        """Reset internal temporal context history."""
        self._context.reset()

    def process(self, frame_batch: FrameBatch) -> Track2Result:
        """
        Execute the full reasoning pipeline on a batch of camera frames.

        Args:
            frame_batch: A FrameBatch containing one or more camera frames.

        Returns:
            Track2Result containing the structured perception, spatial analysis,
            context analysis, assistance decision, and summary.

        Raises:
            TypeError: If input is not a FrameBatch instance.
            ValueError: If FrameBatch is empty.
            GeminiVLMError: If VLM processing fails (never fabricates data on error).
        """
        if not isinstance(frame_batch, FrameBatch):
            raise TypeError(
                f"Track2Pipeline expects a FrameBatch instance, got {type(frame_batch).__name__}"
            )

        if len(frame_batch) == 0:
            raise ValueError("FrameBatch cannot be empty")

        # 1. Vision-Language Model scene understanding
        perception = self._vlm.understand(frame_batch)

        # 2. Image-space spatial reasoning
        spatial = self._spatial.analyze(perception)

        # 3. Context & temporal persistence reasoning
        context = self._context.analyze(spatial, perception, frame_batch)

        # 4. Priority scoring & assistance decision
        decision = self._decision.decide(perception, spatial, context)

        # 5. Build final structured result for Track 3
        summary = (
            f"[{decision.category.value.upper()}] Priority: {decision.priority.value}. "
            f"{decision.message} (Scene: {perception.scene_label})"
        )

        return Track2Result(
            frame_id=perception.frame_id,
            timestamp_ms=perception.timestamp_ms,
            decision=decision,
            perception=perception,
            spatial=spatial,
            context=context,
            summary=summary,
        )
