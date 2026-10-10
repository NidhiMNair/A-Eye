"""
Video frame extraction and dataset manifest generation.

Extracts frame sequences from video files at a configurable target FPS
and creates session manifest CSV records with accurate timestamps.
"""

import csv
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import cv2

logger = logging.getLogger(__name__)


def extract_frames_from_video(
    video_path: Path,
    output_dir: Path,
    session_id: str,
    target_fps: float = 2.0,
    start_sec: float = 0.0,
    end_sec: Optional[float] = None,
    max_frames: Optional[int] = None,
) -> Path:
    """
    Extract frames from a video recording and generate a session manifest.

    Returns path to created manifest CSV.
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0 or not (video_fps > 0):  # Check NaN / non-positive
        logger.warning(f"Video {video_path.name} reported invalid FPS ({video_fps}). Defaulting to 30.0.")
        video_fps = 30.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(round(video_fps / target_fps)))

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.csv"

    start_frame = int(start_sec * video_fps)
    end_frame = int(end_sec * video_fps) if end_sec is not None else (total_frames if total_frames > 0 else float("inf"))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame_idx = start_frame
    extracted_count = 0

    manifest_rows: List[Dict[str, Any]] = []

    logger.info(
        f"Extracting session '{session_id}' from {video_path.name} "
        f"(video_fps={video_fps:.1f}, target_fps={target_fps}, interval={frame_interval})"
    )

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or current_frame_idx > end_frame:
            break

        if (current_frame_idx - start_frame) % frame_interval == 0:
            # Get actual video position timestamp in milliseconds
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            if timestamp_ms <= 0:
                timestamp_ms = int((current_frame_idx / video_fps) * 1000)

            frame_filename = f"frame_{extracted_count:04d}.jpg"
            frame_path = frames_dir / frame_filename

            success = cv2.imwrite(str(frame_path), frame)
            if not success:
                logger.error(f"Failed to write frame to {frame_path}")
                current_frame_idx += 1
                continue

            manifest_rows.append({
                "session_id": session_id,
                "frame_path": str(frame_path.relative_to(output_dir.parent) if output_dir.parent in frame_path.parents else frame_path),
                "frame_index": extracted_count,
                "timestamp_ms": timestamp_ms,
            })

            extracted_count += 1
            if max_frames is not None and extracted_count >= max_frames:
                break

        current_frame_idx += 1

    cap.release()

    if extracted_count == 0:
        logger.warning(f"No frames were extracted from {video_path}")

    # Write manifest CSV
    fieldnames = ["session_id", "frame_path", "frame_index", "timestamp_ms"]
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    logger.info(f"Extracted {extracted_count} frames for session '{session_id}'. Manifest written to {manifest_path}")
    return manifest_path
