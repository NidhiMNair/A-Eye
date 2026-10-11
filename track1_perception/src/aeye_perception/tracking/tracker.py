
"""Simple IoU-based multi-object tracker.

This is a baseline tracker, not a production-grade MOT system.
Motion values represent apparent image-space changes only.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from aeye_perception.contract import DetectedObject, MotionVector
from aeye_perception.geometry import clamp_bbox, compute_center, compute_iou, compute_area


@dataclass
class _Track:
    track_id: int
    label: str
    bbox: List[float]
    center: tuple[float, float]
    area: float
    timestamp_ms: int
    velocity: tuple[float, float] = (0.0, 0.0)
    missed_frames: int = 0


class IoUTracker:
    """Associate detections between frames using class labels and IoU.

    Supports optional constant-velocity motion prediction in image space.
    Note: Motion values represent apparent 2D image-space changes only;
    they do not represent physical 3D velocity or collision risk.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_missed_frames: int = 2,
        use_motion_prediction: bool = True,
    ) -> None:
        if not 0.0 <= iou_threshold <= 1.0:
            raise ValueError("iou_threshold must be between 0 and 1")
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames cannot be negative")

        self.iou_threshold = iou_threshold
        self.max_missed_frames = max_missed_frames
        self.use_motion_prediction = use_motion_prediction
        self._tracks: Dict[int, _Track] = {}
        self._next_id = 1
        self._last_timestamp_ms: Optional[int] = None

    def _predict_bbox(self, track: _Track, dt: float) -> List[float]:
        """Estimate future bbox under constant apparent image velocity."""
        vx, vy = track.velocity
        dx = vx * dt
        dy = vy * dt
        raw = [
            track.bbox[0] + dx,
            track.bbox[1] + dy,
            track.bbox[2] + dx,
            track.bbox[3] + dy,
        ]
        return clamp_bbox(raw)

    def update(
        self,
        detections: List[DetectedObject],
        timestamp_ms: int,
    ) -> List[DetectedObject]:
        """Assign IDs and motion to detections from one frame."""

        if timestamp_ms < 0:
            raise ValueError("timestamp_ms cannot be negative")

        if (
            self._last_timestamp_ms is not None
            and timestamp_ms <= self._last_timestamp_ms
        ):
            raise ValueError("timestamps must increase between updates")

        dt = (
            None
            if self._last_timestamp_ms is None
            else (timestamp_ms - self._last_timestamp_ms) / 1000.0
        )

        # Build all eligible detection/track pairs.
        candidates = []
        for det_index, detection in enumerate(detections):
            for track_id, track in self._tracks.items():
                if detection.label != track.label:
                    continue

                if (
                    self.use_motion_prediction
                    and dt is not None
                    and track.missed_frames == 0
                    and track.velocity != (0.0, 0.0)
                ):
                    pred_bbox = self._predict_bbox(track, dt)
                    overlap = max(
                        compute_iou(detection.bbox, pred_bbox),
                        compute_iou(detection.bbox, track.bbox),
                    )
                else:
                    overlap = compute_iou(detection.bbox, track.bbox)

                if overlap >= self.iou_threshold:
                    candidates.append((overlap, det_index, track_id))

        # Greedy matching: highest IoU first; each track/detection once.
        candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
        matched_detections = set()
        matched_tracks = set()
        matches = {}

        for overlap, det_index, track_id in candidates:
            if det_index in matched_detections or track_id in matched_tracks:
                continue
            matched_detections.add(det_index)
            matched_tracks.add(track_id)
            matches[det_index] = track_id

        output = []
        updated_tracks = {}

        for index, detection in enumerate(detections):
            center = compute_center(detection.bbox)
            area = compute_area(detection.bbox)

            if index in matches:
                track_id = matches[index]
                previous = self._tracks[track_id]
                motion = None
                velocity = (0.0, 0.0)

                # Do not calculate velocity across a missing-frame gap:
                # the number/timing of unseen movements is uncertain.
                if dt is not None and previous.missed_frames == 0:
                    vx = (center[0] - previous.center[0]) / dt
                    vy = (center[1] - previous.center[1]) / dt
                    motion = MotionVector(
                        dx=vx,
                        dy=vy,
                        growth=(area - previous.area) / dt,
                    )
                    velocity = (vx, vy)

                updated_tracks[track_id] = _Track(
                    track_id=track_id,
                    label=detection.label,
                    bbox=list(detection.bbox),
                    center=center,
                    area=area,
                    timestamp_ms=timestamp_ms,
                    velocity=velocity,
                )
            else:
                track_id = self._next_id
                self._next_id += 1
                motion = None

                updated_tracks[track_id] = _Track(
                    track_id=track_id,
                    label=detection.label,
                    bbox=list(detection.bbox),
                    center=center,
                    area=area,
                    timestamp_ms=timestamp_ms,
                    velocity=(0.0, 0.0),
                )

            output.append(
                detection.model_copy(
                    update={"track_id": track_id, "motion": motion}
                )
            )

        # Preserve unmatched tracks briefly so an object can reappear.
        for track_id, track in self._tracks.items():
            if track_id not in matched_tracks:
                track.missed_frames += 1
                if track.missed_frames <= self.max_missed_frames:
                    track.velocity = (0.0, 0.0)
                    updated_tracks[track_id] = track

        self._tracks = updated_tracks
        self._last_timestamp_ms = timestamp_ms
        return output

    def reset(self) -> None:
        """Forget all tracks and restart ID assignment."""
        self._tracks.clear()
        self._next_id = 1
        self._last_timestamp_ms = None
