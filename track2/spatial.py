"""
track2/spatial.py
===================
Deterministic image-space spatial reasoning for Track 2.

Derives 2D image-space spatial relationships from detected bounding boxes:
  - Horizontal zones: left, center, right
  - Vertical zones: upper, middle, lower
  - Central camera view detection
  - Prominence (significant image area/extent)
  - Relative positioning between objects
  - 2D Bounding-box overlap

CONSTRAINTS:
  - Operates purely in 2D image coordinates.
  - Does NOT infer physical distances, depths, or metrics (no "2 meters away").
  - Does NOT claim any area is safe.
  - Fully offline and deterministic (no external AI calls).
"""

from __future__ import annotations

from typing import Optional

from track2.models import (
    BoundingBox,
    DetectedObject,
    HorizontalZone,
    PerceptionResult,
    SpatialAnalysis,
    SpatialObjectInfo,
    VerticalZone,
)

# Thresholds for image-space coordinate classification [0.0, 1.0]
ZONE_LEFT_BOUNDARY = 0.35
ZONE_RIGHT_BOUNDARY = 0.65

ZONE_UPPER_BOUNDARY = 0.35
ZONE_LOWER_BOUNDARY = 0.65

# Prominence thresholds in normalized image units
PROMINENT_MIN_AREA = 0.12
PROMINENT_MIN_DIMENSION = 0.40


class SpatialReasoner:
    """
    Deterministic image-space spatial reasoning engine.
    """

    def analyze(self, perception: PerceptionResult) -> SpatialAnalysis:
        """
        Analyze the bounding boxes and spatial data in a PerceptionResult.

        Args:
            perception: A validated PerceptionResult.

        Returns:
            SpatialAnalysis containing image-space classifications, relative
            positions, overlaps, and central/prominent object lists.
        """
        objects = perception.objects
        spatial_infos: list[SpatialObjectInfo] = []

        for idx, obj in enumerate(objects):
            bbox = obj.bbox
            hz = self._classify_horizontal_zone(bbox)
            vz = self._classify_vertical_zone(bbox)
            is_central = self._check_is_central(bbox)
            is_prominent = self._check_is_prominent(bbox)

            # Compute relative positions and overlaps against other objects in frame
            relative_positions: list[str] = []
            overlapping_labels: list[str] = []

            for other_idx, other_obj in enumerate(objects):
                if idx == other_idx:
                    continue

                # Relative position
                rel = self._describe_relative_position(obj, other_obj)
                if rel:
                    relative_positions.append(rel)

                # Overlap
                if bbox.overlaps(other_obj.bbox):
                    overlapping_labels.append(other_obj.label)

            spatial_infos.append(
                SpatialObjectInfo(
                    label=obj.label,
                    conf=obj.conf,
                    bbox=bbox,
                    horizontal_zone=hz,
                    vertical_zone=vz,
                    is_central=is_central,
                    is_prominent=is_prominent,
                    relative_positions=relative_positions,
                    overlapping_labels=overlapping_labels,
                )
            )

        central_list = [s for s in spatial_infos if s.is_central]
        prominent_list = [s for s in spatial_infos if s.is_prominent]

        uncertainties = list(perception.uncertainties)
        if not spatial_infos:
            uncertainties.append("No objects detected in the visible image space.")

        return SpatialAnalysis(
            frame_id=perception.frame_id,
            objects=spatial_infos,
            central_objects=central_list,
            prominent_objects=prominent_list,
            scene_label=perception.scene_label,
            scene_description=perception.scene_description,
            uncertainties=uncertainties,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_horizontal_zone(bbox: BoundingBox) -> HorizontalZone:
        """Classify center point into left, center, or right image-space zone."""
        cx = bbox.center_x
        if cx < ZONE_LEFT_BOUNDARY:
            return HorizontalZone.LEFT
        elif cx > ZONE_RIGHT_BOUNDARY:
            return HorizontalZone.RIGHT
        return HorizontalZone.CENTER

    @staticmethod
    def _classify_vertical_zone(bbox: BoundingBox) -> VerticalZone:
        """Classify center point into upper, middle, or lower image-space zone."""
        cy = bbox.center_y
        if cy < ZONE_UPPER_BOUNDARY:
            return VerticalZone.UPPER
        elif cy > ZONE_LOWER_BOUNDARY:
            return VerticalZone.LOWER
        return VerticalZone.MIDDLE

    @staticmethod
    def _check_is_central(bbox: BoundingBox) -> bool:
        """
        Check if object spans or is centered in the central camera view.
        Returns True if center_x is in central zone or box spans across the center.
        """
        if ZONE_LEFT_BOUNDARY <= bbox.center_x <= ZONE_RIGHT_BOUNDARY:
            return True
        # Object spans across the central zone
        if bbox.x_min < ZONE_LEFT_BOUNDARY and bbox.x_max > ZONE_RIGHT_BOUNDARY:
            return True
        return False

    @staticmethod
    def _check_is_prominent(bbox: BoundingBox) -> bool:
        """Check if object occupies a substantial portion of the camera frame."""
        return (
            bbox.area >= PROMINENT_MIN_AREA
            or bbox.width >= PROMINENT_MIN_DIMENSION
            or bbox.height >= PROMINENT_MIN_DIMENSION
        )

    @staticmethod
    def _describe_relative_position(obj_a: DetectedObject, obj_b: DetectedObject) -> Optional[str]:
        """Describe 2D spatial relationship from object A to object B."""
        box_a = obj_a.bbox
        box_b = obj_b.bbox

        horizontal_rel: Optional[str] = None
        if box_a.x_max <= box_b.x_min:
            horizontal_rel = f"{obj_a.label} is to the left of {obj_b.label}"
        elif box_a.x_min >= box_b.x_max:
            horizontal_rel = f"{obj_a.label} is to the right of {obj_b.label}"

        vertical_rel: Optional[str] = None
        if box_a.y_max <= box_b.y_min:
            vertical_rel = f"{obj_a.label} is above {obj_b.label}"
        elif box_a.y_min >= box_b.y_max:
            vertical_rel = f"{obj_a.label} is below {obj_b.label}"

        if horizontal_rel and vertical_rel:
            return f"{horizontal_rel} and {vertical_rel}"
        return horizontal_rel or vertical_rel
