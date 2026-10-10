"""
track2/context.py
===================
Conservative context reasoning for Track 2.

Interprets the current observation in context of preceding observations
or multi-frame batches without inventing external sensor state.

Answers:
  - Is an observation persistent across frames?
  - Is an object newly observed?
  - Is an object consistently in the central camera view?
  - Are there relevant changes between observations?
  - Are there repeated hazards?

CONSTRAINTS:
  - Conservative temporal comparison.
  - Does NOT invent sensor data (no GPS, IMU, depth cameras, biometrics).
  - Does NOT assert physical movement when visual data only reflects camera movement.
"""

from __future__ import annotations

from typing import Optional

from track2.models import (
    ContextAnalysis,
    FrameBatch,
    PerceptionResult,
    SpatialAnalysis,
)


class ContextReasoner:
    """
    Conservative context engine maintaining a small sliding history of observations.
    """

    def __init__(self, max_history: int = 5) -> None:
        self._max_history = max_history
        self._history: list[SpatialAnalysis] = []
        self._hazard_history: list[list[str]] = []

    def reset(self) -> None:
        """Reset internal history state."""
        self._history.clear()
        self._hazard_history.clear()

    def analyze(
        self,
        spatial: SpatialAnalysis,
        perception: PerceptionResult,
        frame_batch: Optional[FrameBatch] = None,
    ) -> ContextAnalysis:
        """
        Derive contextual relationships between the current observation and past frames.

        Args:
            spatial: Current image-space spatial analysis.
            perception: Current VLM perception result.
            frame_batch: Optional FrameBatch providing batch frame count.

        Returns:
            ContextAnalysis summarizing persistence, newly observed objects,
            central persistence, and observed changes.
        """
        frame_count = len(frame_batch) if frame_batch is not None else 1
        current_labels = {obj.label for obj in spatial.objects}
        current_central_labels = {obj.label for obj in spatial.central_objects}
        current_hazards = perception.hazards

        persistent_objects: set[str] = set()
        new_objects: set[str] = set()
        central_persistence: set[str] = set()
        repeated_hazards: set[str] = set()
        changes: list[str] = []

        if not self._history:
            # First observation: all detected objects are newly observed
            new_objects = current_labels
            changes.append("Baseline observation established.")
            is_multi_frame = frame_count > 1
        else:
            is_multi_frame = True
            prev_spatial = self._history[-1]
            prev_labels = {obj.label for obj in prev_spatial.objects}
            prev_central_labels = {obj.label for obj in prev_spatial.central_objects}

            # 1. Persistence & New items
            for label in current_labels:
                if label in prev_labels:
                    persistent_objects.add(label)
                else:
                    new_objects.add(label)

            # 2. Central view persistence
            for label in current_central_labels:
                if label in prev_central_labels:
                    central_persistence.add(label)

            # 3. Repeated hazards
            for hazard in current_hazards:
                for past_hazard_list in self._hazard_history:
                    if hazard in past_hazard_list:
                        repeated_hazards.add(hazard)

            # 4. Conservative change tracking
            for n in new_objects:
                changes.append(f"Newly observed in scene: {n}")
            for c in central_persistence:
                changes.append(f"Consistently in central view: {c}")
            if prev_spatial.scene_label != spatial.scene_label:
                changes.append(
                    f"Scene category changed from '{prev_spatial.scene_label}' to '{spatial.scene_label}'"
                )

        # Update sliding history
        self._history.append(spatial)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        self._hazard_history.append(current_hazards)
        if len(self._hazard_history) > self._max_history:
            self._hazard_history.pop(0)

        return ContextAnalysis(
            is_multi_frame=is_multi_frame,
            frame_count=max(frame_count, len(self._history)),
            persistent_objects=sorted(list(persistent_objects)),
            new_objects=sorted(list(new_objects)),
            central_persistence=sorted(list(central_persistence)),
            repeated_hazards=sorted(list(repeated_hazards)),
            changes=changes,
        )
