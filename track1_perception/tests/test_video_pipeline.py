"""
Unit and integration tests for the video perception inference pipeline.

Tests process_video, annotate_frame, timestamp handling, JSONL output, and CLI entry point
using MockDetector and synthetic video captures (no model downloads or network calls).
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import cv2
import numpy as np
import pytest

from aeye_perception.contract import DetectedObject, MotionVector, PerceptionResult
from aeye_perception.detection.base import MockDetector
from aeye_perception.pipeline import annotate_frame, process_video
from aeye_perception.tracking.tracker import IoUTracker


def create_synthetic_test_video(path: Path, num_frames: int = 5, fps: float = 10.0) -> Path:
    """Helper to generate a small synthetic MP4 video file for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    for i in range(num_frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * (40 + i * 20)
        cv2.circle(frame, (50 + i * 20, 100), 25, (0, 255, 0), -1)
        writer.write(frame)

    writer.release()
    return path


def test_process_video_end_to_end_with_mock_detector(tmp_path):
    """End-to-end test of process_video with MockDetector, JSONL output, and annotated video."""
    video_path = tmp_path / "test_input.mp4"
    jsonl_path = tmp_path / "output_results.jsonl"
    video_out_path = tmp_path / "output_annotated.mp4"

    create_synthetic_test_video(video_path, num_frames=5, fps=10.0)

    # Moving chair across frames
    custom_dets = [
        DetectedObject(
            label="chair",
            conf=0.90,
            bbox=[0.20, 0.20, 0.40, 0.40],
        )
    ]
    detector = MockDetector(preset_objects=custom_dets)
    tracker = IoUTracker()

    results = process_video(
        video_path=video_path,
        detector=detector,
        tracker=tracker,
        output_jsonl=jsonl_path,
        output_video=video_out_path,
    )

    # 1. Output count and frame progression
    assert len(results) == 5
    for idx, res in enumerate(results):
        assert res.frame_id == idx
        assert res.source == "offline"
        assert res.text_blocks == []
        assert res.scene_label is None
        assert res.scene_description is None
        assert len(res.objects) == 1
        assert res.objects[0].track_id == 1  # Track identity maintained across frames

    # 2. Strict timestamp monotonicity
    for i in range(1, len(results)):
        assert results[i].timestamp_ms > results[i - 1].timestamp_ms

    # 3. JSONL output verification
    assert jsonl_path.exists()
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
    for idx, line in enumerate(lines):
        parsed = PerceptionResult.from_json(line)
        assert parsed.frame_id == idx
        assert parsed.objects[0].track_id == 1

    # 4. Output video verification
    assert video_out_path.exists()
    assert video_out_path.stat().st_size > 0


def test_process_video_handles_duplicate_or_zero_timestamps(tmp_path):
    """Verify that video containers with zero or duplicate timestamps advance strictly."""
    video_path = tmp_path / "test_duplicate_ts.mp4"
    create_synthetic_test_video(video_path, num_frames=4, fps=20.0)

    # Mock VideoCapture to return constant 0.0 for CAP_PROP_POS_MSEC
    real_cap = cv2.VideoCapture(str(video_path))
    real_fps = real_cap.get(cv2.CAP_PROP_FPS) or 20.0

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: (
        real_fps if prop == cv2.CAP_PROP_FPS else (0.0 if prop == cv2.CAP_PROP_POS_MSEC else 320)
    )
    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mock_cap.read.side_effect = [
        (True, dummy_frame),
        (True, dummy_frame),
        (True, dummy_frame),
        (True, dummy_frame),
        (False, None),
    ]

    with patch("cv2.VideoCapture", return_value=mock_cap):
        results = process_video(
            video_path=video_path,
            detector=MockDetector(),
        )

    real_cap.release()

    assert len(results) == 4
    # All timestamps must increase strictly despite metadata reporting 0
    for i in range(1, len(results)):
        assert results[i].timestamp_ms > results[i - 1].timestamp_ms
        # Expected interval is at least round(1000.0 / 20.0) = 50ms
        assert results[i].timestamp_ms - results[i - 1].timestamp_ms >= 50


def test_process_video_handles_raw_timestamp_rounding_to_same_integer(tmp_path):
    """Regression test: verify timestamps strictly increase when raw float timestamps round to the same integer.

    E.g., if frame 0 is at 100.0ms, and frame 1 reports 100.2ms, round(100.2) is 100, which without
    fallback would equal the previous integer timestamp and cause tracker association failure.
    """
    video_path = tmp_path / "test_rounding_ts.mp4"
    create_synthetic_test_video(video_path, num_frames=4, fps=25.0)

    raw_timestamps = [100.0, 100.2, 100.4, 200.0]

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    current_idx = [0]

    def mock_get(prop):
        if prop == cv2.CAP_PROP_FPS:
            return 25.0
        elif prop == cv2.CAP_PROP_POS_MSEC:
            idx = max(0, min(current_idx[0] - 1, len(raw_timestamps) - 1))
            return raw_timestamps[idx]
        elif prop == cv2.CAP_PROP_FRAME_WIDTH:
            return 320
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return 240
        return 0

    mock_cap.get.side_effect = mock_get

    dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)

    def mock_read():
        if current_idx[0] < len(raw_timestamps):
            current_idx[0] += 1
            return (True, dummy_frame)
        return (False, None)

    mock_cap.read.side_effect = mock_read

    with patch("cv2.VideoCapture", return_value=mock_cap):
        results = process_video(
            video_path=video_path,
            detector=MockDetector(),
        )

    assert len(results) == 4
    # Verify every emitted timestamp is strictly increasing
    for i in range(1, len(results)):
        assert results[i].timestamp_ms > results[i - 1].timestamp_ms

    assert results[0].timestamp_ms == 100
    assert results[1].timestamp_ms == 140
    assert results[2].timestamp_ms == 180
    assert results[3].timestamp_ms == 200


def test_process_video_missing_file_raises_error(tmp_path):
    """Attempting to process a non-existent video path raises FileNotFoundError."""
    missing_path = tmp_path / "does_not_exist.mp4"
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        process_video(video_path=missing_path, detector=MockDetector())


def test_process_video_unreadable_file_raises_error(tmp_path):
    """An empty or unreadable video file raises RuntimeError and releases resources."""
    corrupt_path = tmp_path / "corrupt.mp4"
    corrupt_path.write_bytes(b"not a valid video stream")

    with pytest.raises(RuntimeError, match="Unable to open or decode video file"):
        process_video(video_path=corrupt_path, detector=MockDetector())


def test_process_video_max_frames_limit(tmp_path):
    """Processing with max_frames limits total frames extracted and processed."""
    video_path = tmp_path / "test_limit.mp4"
    create_synthetic_test_video(video_path, num_frames=10, fps=10.0)

    results = process_video(
        video_path=video_path,
        detector=MockDetector(),
        max_frames=3,
    )
    assert len(results) == 3
    assert results[-1].frame_id == 2


def test_annotate_frame_rendering():
    """Verify annotate_frame draws bounding boxes, labels, track IDs, and motion vectors."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    obj_with_motion = DetectedObject(
        label="person",
        conf=0.88,
        bbox=[0.1, 0.1, 0.4, 0.5],
        track_id=42,
        motion=MotionVector(dx=0.05, dy=-0.02, growth=0.01),
    )
    obj_without_motion = DetectedObject(
        label="chair",
        conf=0.75,
        bbox=[0.6, 0.6, 0.9, 0.9],
        track_id=None,
        motion=None,
    )

    annotated = annotate_frame(frame, [obj_with_motion, obj_without_motion])
    assert isinstance(annotated, np.ndarray)
    assert annotated.shape == (480, 640, 3)
    # Check that drawing actually modified pixels
    assert np.any(annotated > 0)


def test_run_video_pipeline_cli_mock_mode(tmp_path):
    """Test CLI execution with --mock and synthetic video."""
    video_path = tmp_path / "cli_input.mp4"
    jsonl_path = tmp_path / "cli_output.jsonl"
    create_synthetic_test_video(video_path, num_frames=3, fps=10.0)

    cmd = [
        sys.executable,
        "scripts/run_video_pipeline.py",
        "--video",
        str(video_path),
        "--mock",
        "--output-jsonl",
        str(jsonl_path),
        "--max-frames",
        "2",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    assert res.returncode == 0
    assert jsonl_path.exists()
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_run_video_pipeline_cli_missing_video(tmp_path):
    """Test CLI execution with nonexistent video exits with code 1 and concise error message."""
    cmd = [
        sys.executable,
        "scripts/run_video_pipeline.py",
        "--video",
        str(tmp_path / "non_existent.mp4"),
        "--mock",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    assert res.returncode == 1
    assert "Error: Input video file not found" in res.stdout
