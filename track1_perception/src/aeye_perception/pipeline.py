"""
Video perception inference pipeline for A-Eye Track 1.

Connects obstacle detection (YOLOObstacleDetector / MockDetector),
multi-object tracking (IoUTracker), and the unified PerceptionResult contract.
"""

import json
import logging
from pathlib import Path
from typing import Iterator, List, Optional, Union
import cv2
import numpy as np

from aeye_perception.contract import DetectedObject, PerceptionResult
from aeye_perception.detection.base import AbstractDetector
from aeye_perception.geometry import denormalize_bbox
from aeye_perception.tracking.tracker import IoUTracker

logger = logging.getLogger(__name__)


def annotate_frame(frame: np.ndarray, objects: List[DetectedObject]) -> np.ndarray:
    """Draw bounding boxes, track IDs, labels, and motion vectors on a BGR frame."""
    annotated = frame.copy()
    img_h, img_w = frame.shape[:2]

    for obj in objects:
        x1, y1, x2, y2 = denormalize_bbox(obj.bbox, img_w, img_h)

        if obj.track_id is not None:
            label_text = f"#{obj.track_id} {obj.label} ({obj.conf:.2f})"
        else:
            label_text = f"{obj.label} ({obj.conf:.2f})"

        # Color: Green box
        color = (0, 255, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        bg_y1 = max(0, y1 - 20)
        bg_y2 = y1
        cv2.rectangle(annotated, (x1, bg_y1), (x1 + tw + 4, bg_y2), color, -1)
        cv2.putText(
            annotated,
            label_text,
            (x1 + 2, max(12, y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
        )

        # Motion indicator if present
        if obj.motion is not None:
            motion_text = f"dx:{obj.motion.dx:+.2f} dy:{obj.motion.dy:+.2f}"
            cv2.putText(
                annotated,
                motion_text,
                (x1 + 2, min(img_h - 4, y2 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 255, 255),
                1,
            )

    return annotated


def process_video(
    video_path: Union[str, Path],
    detector: AbstractDetector,
    tracker: Optional[IoUTracker] = None,
    output_jsonl: Optional[Union[str, Path]] = None,
    output_video: Optional[Union[str, Path]] = None,
    conf_threshold: Optional[float] = None,
    iou_threshold: Optional[float] = None,
    max_frames: Optional[int] = None,
) -> List[PerceptionResult]:
    """Process a video file frame-by-frame through detector and tracker.

    Parameters:
    - video_path: Path to input video file.
    - detector: Initialized obstacle detector (AbstractDetector instance).
    - tracker: Optional IoUTracker instance (creates new IoUTracker() if None).
    - output_jsonl: Optional path to save JSONL output (one PerceptionResult per line).
    - output_video: Optional path to save annotated MP4 video.
    - conf_threshold: Optional confidence threshold override.
    - iou_threshold: Optional detector NMS IoU threshold override.
    - max_frames: Optional frame limit.

    Returns:
    - List of PerceptionResult instances for each processed frame.
    """
    v_path = Path(video_path)
    if not v_path.exists():
        raise FileNotFoundError(f"Video file not found at '{v_path}'")

    cap = cv2.VideoCapture(str(v_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open or decode video file: '{v_path}'")

    if tracker is None:
        tracker = IoUTracker()

    writer = None
    jsonl_f = None
    results: List[PerceptionResult] = []

    try:
        # Determine video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0 or np.isnan(video_fps):
            logger.warning(
                f"Video '{v_path.name}' reported invalid FPS ({video_fps}). Defaulting to 30.0 FPS."
            )
            video_fps = 30.0

        frame_dt_ms = max(1, int(round(1000.0 / video_fps)))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Setup output JSONL if requested
        if output_jsonl:
            out_jsonl_path = Path(output_jsonl)
            out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            jsonl_f = open(out_jsonl_path, "w", encoding="utf-8")

        # Setup output video if requested
        if output_video:
            out_vid_path = Path(output_video)
            out_vid_path.parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(out_vid_path), fourcc, video_fps, (width, height))
            if not writer.isOpened():
                # Fallback fourcc codec if mp4v fails
                fourcc = cv2.VideoWriter_fourcc(*"avc1")
                writer = cv2.VideoWriter(str(out_vid_path), fourcc, video_fps, (width, height))

        frame_idx = 0
        last_timestamp_ms: Optional[int] = None

        while cap.isOpened():
            if max_frames is not None and frame_idx >= max_frames:
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # Handle timestamps carefully:
            # Container timestamps (CAP_PROP_POS_MSEC) can be 0, negative, jitter, duplicate,
            # or round to the same integer as the previous frame.
            # Guarantee strictly increasing integer timestamps for the tracker.
            raw_pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            has_valid_raw = (
                raw_pos_msec is not None
                and not np.isnan(raw_pos_msec)
                and raw_pos_msec >= 0
            )

            if last_timestamp_ms is None:
                # First frame: non-negative integer timestamp
                if has_valid_raw and raw_pos_msec > 0:
                    current_ts = max(0, int(round(raw_pos_msec)))
                else:
                    current_ts = 0
            else:
                if has_valid_raw:
                    candidate_ts = int(round(raw_pos_msec))
                    if candidate_ts > last_timestamp_ms:
                        current_ts = candidate_ts
                    else:
                        # Duplicate, backwards, or rounds to <= last_timestamp_ms
                        current_ts = last_timestamp_ms + frame_dt_ms
                else:
                    # Invalid, negative, or NaN timestamp
                    current_ts = last_timestamp_ms + frame_dt_ms

            last_timestamp_ms = current_ts

            # 1. Detection
            raw_detections = detector.detect(
                frame,
                conf_threshold=conf_threshold,
                iou_threshold=iou_threshold,
            )

            # 2. Tracking
            tracked_objects = tracker.update(raw_detections, timestamp_ms=current_ts)

            # 3. Create contract PerceptionResult
            result = PerceptionResult(
                frame_id=frame_idx,
                timestamp_ms=current_ts,
                source="offline",
                objects=tracked_objects,
                text_blocks=[],
                scene_label=None,
                scene_description=None,
            )
            results.append(result)

            # 4. Write JSONL line
            if jsonl_f is not None:
                jsonl_f.write(result.model_dump_json() + "\n")

            # 5. Write annotated video frame
            if writer is not None and writer.isOpened():
                annotated = annotate_frame(frame, tracked_objects)
                writer.write(annotated)

            frame_idx += 1

    finally:
        # Guarantee safe resource release
        cap.release()
        if writer is not None:
            writer.release()
        if jsonl_f is not None:
            jsonl_f.close()

    logger.info(
        f"Processed {len(results)} frame(s) from '{v_path.name}' "
        f"(total elapsed video time: {last_timestamp_ms if last_timestamp_ms is not None else 0} ms)"
    )
    return results
