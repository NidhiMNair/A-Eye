"""
CLI entry point for running the video perception inference pipeline.

Processes a video file frame-by-frame, runs obstacle detection and multi-object
tracking, and emits contract-compliant PerceptionResult records to JSONL.

Usage:
  python scripts/run_video_pipeline.py --video sample.mp4 --mock --output-jsonl results.jsonl
  python scripts/run_video_pipeline.py --video sample.mp4 --weights models/yolov8n.pt --output-jsonl results.jsonl --output-video annotated.mp4
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add src to path for direct script invocation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.detection.base import MockDetector
from aeye_perception.pipeline import process_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_video_pipeline")


def main():
    parser = argparse.ArgumentParser(
        description="Run perception pipeline (detection + tracking) on a video."
    )
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use MockDetector instead of YOLO (runs offline without weights)",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="yolov8n.pt",
        help="Path to YOLO model weights file (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--custom-labels",
        action="store_true",
        help="Apply custom class ID mapping from detector_labels.yaml",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=None,
        help="Confidence threshold override [0.0, 1.0]",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=None,
        help="Detector NMS IoU threshold override [0.0, 1.0]",
    )
    parser.add_argument(
        "--output-jsonl",
        type=str,
        default=None,
        help="Save PerceptionResult records as JSONL (one JSON per line)",
    )
    parser.add_argument(
        "--output-video",
        type=str,
        default=None,
        help="Save annotated MP4 video with bounding boxes and track IDs",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of frames to process",
    )

    args = parser.parse_args()

    # 1. Validate video input path
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Input video file not found at '{video_path}'")
        sys.exit(1)

    # 2. Initialize detector
    if args.mock:
        logger.info("Initializing MockDetector (offline synthetic detection mode)")
        detector = MockDetector()
    else:
        try:
            from aeye_perception.detection.yolo_detector import YOLOObstacleDetector

            detector = YOLOObstacleDetector(
                model_path=args.weights,
                conf_threshold=args.conf,
                iou_threshold=args.iou,
                use_custom_labels=args.custom_labels,
            )
        except ImportError as e:
            logger.error(str(e))
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # 3. Execute pipeline
    t0 = time.time()
    try:
        results = process_video(
            video_path=video_path,
            detector=detector,
            output_jsonl=args.output_jsonl,
            output_video=args.output_video,
            conf_threshold=args.conf,
            iou_threshold=args.iou,
            max_frames=args.max_frames,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline processing failed: {e}")
        sys.exit(1)

    total_time = time.time() - t0
    fps = len(results) / total_time if total_time > 0 else 0.0

    logger.info(
        f"Processing completed: {len(results)} frames in {total_time:.2f}s ({fps:.1f} FPS)"
    )
    if args.output_jsonl:
        logger.info(f"Saved PerceptionResult JSONL to '{args.output_jsonl}'")
    if args.output_video:
        logger.info(f"Saved annotated video to '{args.output_video}'")


if __name__ == "__main__":
    main()
