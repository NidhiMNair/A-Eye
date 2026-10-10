"""
CLI entry point for video frame extraction and manifest generation.

Usage:
  python scripts/extract_frames.py --video path/to/video.mp4 --session-id 20261012_corridorA_01 --output-dir data/raw/20261012_corridorA_01 --fps 2
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.data.frame_extraction import extract_frames_from_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Extract frames from video and generate session manifest CSV.")
    parser.add_argument("--video", type=str, required=True, help="Path to input video recording")
    parser.add_argument("--session-id", type=str, required=True, help="Session identifier (<YYYYMMDD>_<location>_<NN>)")
    parser.add_argument("--output-dir", type=str, required=True, help="Output session directory")
    parser.add_argument("--fps", type=float, default=2.0, help="Target extraction FPS (default: 2.0)")
    parser.add_argument("--start", type=float, default=0.0, help="Start time in seconds")
    parser.add_argument("--end", type=float, default=None, help="End time in seconds")
    parser.add_argument("--max-frames", type=int, default=None, help="Maximum frames to extract")

    args = parser.parse_args()

    try:
        manifest_path = extract_frames_from_video(
            video_path=Path(args.video),
            output_dir=Path(args.output_dir),
            session_id=args.session_id,
            target_fps=args.fps,
            start_sec=args.start,
            end_sec=args.end,
            max_frames=args.max_frames,
        )
        print(f"Extraction complete! Manifest: {manifest_path}")
    except Exception as e:
        logging.error(f"Frame extraction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
