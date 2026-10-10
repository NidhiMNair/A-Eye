"""
Generate synthetic video clips and frame sequences with known ground-truth motion.

THIS SCRIPT GENERATES SYNTHETIC / MOCK TEST FIXTURES ONLY.
DO NOT USE SYNTHETIC METRICS FOR FINAL MODEL BENCHMARKING.
"""

import argparse
import json
import logging
from pathlib import Path
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("synthetic_fixtures")


def generate_synthetic_clip(
    output_dir: Path,
    num_frames: int = 30,
    fps: int = 10,
    width: int = 640,
    height: int = 480,
    seed: int = 42,
) -> Path:
    """
    Generate a synthetic video of a blue rectangle moving rightward (+dx)
    and a green rectangle expanding (+growth).
    """
    np.random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "synthetic_mock_clip.mp4"
    json_path = output_dir / "synthetic_ground_truth.json"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    ground_truth_records = []

    # Initial positions (pixels)
    # Box 1: Chair moving right (+dx)
    b1_x1, b1_y1, b1_w, b1_h = 50.0, 100.0, 80.0, 120.0
    vx1_px_per_sec = 100.0  # 100 pixels per sec rightward

    # Box 2: Table growing (+growth)
    b2_x1, b2_y1, b2_w, b2_h = 300.0, 200.0, 100.0, 80.0
    growth_rate_per_sec = 20.0  # width/height expansion per sec

    dt = 1.0 / fps

    for i in range(num_frames):
        timestamp_ms = int(i * dt * 1000)
        frame = np.ones((height, width, 3), dtype=np.uint8) * 240  # light grey background

        # Draw Box 1 (Blue) - Chair
        x1_1 = int(b1_x1 + i * vx1_px_per_sec * dt)
        y1_1 = int(b1_y1)
        x2_1 = int(x1_1 + b1_w)
        y2_1 = int(y1_1 + b1_h)
        cv2.rectangle(frame, (x1_1, y1_1), (x2_1, y2_1), (255, 0, 0), -1)

        # Draw Box 2 (Green) - Table
        w2_curr = b2_w + i * growth_rate_per_sec * dt
        h2_curr = b2_h + i * growth_rate_per_sec * dt
        x1_2 = int(b2_x1 - (w2_curr - b2_w) / 2)
        y1_2 = int(b2_y1 - (h2_curr - b2_h) / 2)
        x2_2 = int(x1_2 + w2_curr)
        y2_2 = int(y1_2 + h2_curr)
        cv2.rectangle(frame, (x1_2, y1_2), (x2_2, y2_2), (0, 200, 0), -1)

        # Add text label overlay for verification
        cv2.putText(frame, "MOCK SYNTHETIC FIXTURE", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

        # Calculate normalized bounding boxes
        norm_b1 = [x1_1 / width, y1_1 / height, x2_1 / width, y2_1 / height]
        norm_b2 = [x1_2 / width, y1_2 / height, x2_2 / width, y2_2 / height]

        record = {
            "frame_id": i,
            "timestamp_ms": timestamp_ms,
            "is_mock": True,
            "objects": [
                {"label": "chair", "bbox": [round(x, 4) for x in norm_b1], "track_id": 1},
                {"label": "table", "bbox": [round(x, 4) for x in norm_b2], "track_id": 2},
            ],
        }
        ground_truth_records.append(record)

    out.release()

    with open(json_path, "w") as f:
        json.dump(ground_truth_records, f, indent=2)

    logger.info(f"Generated synthetic clip: {video_path}")
    logger.info(f"Generated synthetic ground truth: {json_path}")
    return video_path


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic video fixtures for testing.")
    parser.add_argument("--output-dir", type=str, default="fixtures/synthetic", help="Output directory for fixtures")
    parser.add_argument("--frames", type=int, default=30, help="Number of frames to generate")
    parser.add_argument("--fps", type=int, default=10, help="Frames per second")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    generate_synthetic_clip(out_dir, num_frames=args.frames, fps=args.fps)


if __name__ == "__main__":
    main()
