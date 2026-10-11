"""
CLI entry point for running single-image obstacle detection.

Runs detector inference on a given input image or mock synthetic frame
and emits a contract-compliant PerceptionResult JSON output.

Usage:
  python scripts/run_detector.py --mock --json
  python scripts/run_detector.py --image path/to/image.jpg --output-json result.json --output-image annotated.jpg
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.contract import PerceptionResult, CONTRACT_VERSION
from aeye_perception.detection.base import MockDetector
from aeye_perception.geometry import denormalize_bbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_detector")


def draw_bounding_boxes(image: np.ndarray, objects: list) -> np.ndarray:
    """Draw bounding boxes and class labels on an image frame."""
    annotated = image.copy()
    img_h, img_w = image.shape[:2]

    for obj in objects:
        x1, y1, x2, y2 = denormalize_bbox(obj.bbox, img_w, img_h)
        label_text = f"{obj.label} ({obj.conf:.2f})"

        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Draw background label box
        (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x1, max(0, y1 - 20)), (x1 + tw + 4, y1), (0, 255, 0), -1)
        cv2.putText(annotated, label_text, (x1 + 2, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    return annotated


def main():
    parser = argparse.ArgumentParser(description="Run object detector on a single image.")
    parser.add_argument("--image", type=str, default=None, help="Path to input BGR image file")
    parser.add_argument("--mock", action="store_true", help="Use MockDetector with synthetic test frame")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Path to model weights file")
    parser.add_argument("--custom-labels", action="store_true", help="Apply custom class ID mapping from detector_labels.yaml (for custom models only)")
    parser.add_argument("--conf", type=float, default=None, help="Confidence threshold override [0.0, 1.0]")
    parser.add_argument("--iou", type=float, default=None, help="NMS IoU threshold override [0.0, 1.0]")
    parser.add_argument("--output-json", type=str, default=None, help="Save PerceptionResult JSON to file")
    parser.add_argument("--output-image", type=str, default=None, help="Save annotated frame image to file")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output to stdout")

    args = parser.parse_args()

    if not args.mock and not args.image:
        print("Error: Specify either --image <path> or --mock mode.")
        sys.exit(1)

    # 1. Prepare image
    if args.mock:
        logger.info("Running detector in MOCK synthetic image mode")
        img = np.ones((480, 640, 3), dtype=np.uint8) * 240
        detector = MockDetector()
    else:
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"Error: Input image file not found at {img_path}")
            sys.exit(1)

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"Error: Unable to decode image file at {img_path}")
            sys.exit(1)

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

    # 2. Run detector inference
    try:
        t0 = time.time()
        detected_objects = detector.detect(img, conf_threshold=args.conf, iou_threshold=args.iou)
        latency_ms = (time.time() - t0) * 1000.0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    timestamp_ms = int(time.time() * 1000)
    result = PerceptionResult(
        frame_id=0,
        timestamp_ms=timestamp_ms,
        source="offline",
        objects=detected_objects,
        text_blocks=[],
        scene_label=None,
        scene_description=None,
    )

    logger.info(
        f"Inference complete: detected {len(detected_objects)} object(s) "
        f"in {latency_ms:.1f} ms (Host CPU execution)"
    )

    # 3. Handle outputs
    if args.json:
        print(result.to_json())

    if args.output_json:
        out_json_path = Path(args.output_json)
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json_path, "w") as f:
            f.write(result.to_json())
        logger.info(f"Saved PerceptionResult JSON to {out_json_path}")

    if args.output_image:
        out_img_path = Path(args.output_image)
        out_img_path.parent.mkdir(parents=True, exist_ok=True)
        annotated = draw_bounding_boxes(img, detected_objects)
        cv2.imwrite(str(out_img_path), annotated)
        logger.info(f"Saved annotated image to {out_img_path}")


if __name__ == "__main__":
    main()
