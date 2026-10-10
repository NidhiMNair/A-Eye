"""
CLI script emitting a stream of synthetic/mock PerceptionResult JSON messages.

Allows Tracks 2 (Reasoning) and 3 (App/UI) to integrate and test contract
deserialization before full ML model baselines are trained.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add src to path for direct invocation without setup.py install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.contract import (
    PerceptionResult,
    DetectedObject,
    TextBlock,
    MotionVector,
    CONTRACT_VERSION,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mock_stream")


def generate_mock_sequence(count: int = 10, fps: float = 2.0, jsonl: bool = True):
    """
    Generate and stream synthetic PerceptionResult records.
    """
    start_time_ms = int(time.time() * 1000)
    dt_ms = int(1000.0 / fps)

    logger.info(f"Starting mock perception stream (count={count}, fps={fps}, contract={CONTRACT_VERSION})")
    logger.info("--- STREAM BEGIN ---")

    for i in range(count):
        timestamp_ms = start_time_ms + (i * dt_ms)

        # Alternate between offline detection frames with motion and frames with text blocks
        if i % 2 == 0:
            objects = [
                DetectedObject(
                    label="chair",
                    conf=0.88,
                    bbox=[0.35 + (i * 0.01), 0.45, 0.55 + (i * 0.01), 0.85],
                    track_id=10,
                    motion=MotionVector(dx=0.02, dy=0.0, growth=0.005),
                ),
                DetectedObject(
                    label="door",
                    conf=0.94,
                    bbox=[0.05, 0.10, 0.30, 0.90],
                    track_id=None,
                    motion=None,
                ),
            ]
            text_blocks = []
            scene_label = "corridor"
        else:
            objects = [
                DetectedObject(
                    label="person",
                    conf=0.76,
                    bbox=[0.60, 0.30, 0.80, 0.90],
                    track_id=14,
                    motion=MotionVector(dx=-0.04, dy=0.01, growth=-0.002),
                )
            ]
            text_blocks = [
                TextBlock(
                    text="Room 302 - CSE Lab",
                    conf=0.93,
                    bbox=[0.15, 0.25, 0.45, 0.35],
                )
            ]
            scene_label = "room"

        result = PerceptionResult(
            frame_id=i,
            timestamp_ms=timestamp_ms,
            source="offline",
            objects=objects,
            text_blocks=text_blocks,
            scene_label=scene_label,
            scene_description=None,  # Must be None for offline
        )

        if jsonl:
            print(result.model_dump_json())
        else:
            print(result.to_json())
            print("=" * 40)

        sys.stdout.flush()
        if fps > 0 and i < count - 1:
            time.sleep(1.0 / fps)

    logger.info("--- STREAM END ---")


def main():
    parser = argparse.ArgumentParser(description="Emit a stream of mock PerceptionResult JSON objects.")
    parser.add_argument("--count", type=int, default=10, help="Number of frames to emit")
    parser.add_argument("--fps", type=float, default=2.0, help="Emission rate in frames per second")
    parser.add_argument("--jsonl", action="store_true", help="Format output as one JSON per line (JSONL)")
    args = parser.parse_args()

    generate_mock_sequence(count=args.count, fps=args.fps, jsonl=args.jsonl)


if __name__ == "__main__":
    main()
