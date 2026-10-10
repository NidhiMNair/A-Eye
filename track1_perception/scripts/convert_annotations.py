"""
CLI entry point for dataset annotation format conversion (COCO <-> YOLO).

Usage:
  python scripts/convert_annotations.py --mode coco2yolo --input annotations.json --output data/raw/session1/annotations
  python scripts/convert_annotations.py --mode yolo2coco --input data/raw/session1/annotations --images-info info.json --output annotations.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.data.converters import coco_to_yolo, yolo_to_coco

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Convert annotation formats between COCO JSON and YOLO txt.")
    parser.add_argument("--mode", type=str, choices=["coco2yolo", "yolo2coco"], required=True, help="Conversion mode")
    parser.add_argument("--input", type=str, required=True, help="Input file or directory path")
    parser.add_argument("--output", type=str, required=True, help="Output directory or JSON file path")
    parser.add_argument("--labels-config", type=str, default="configs/detector_labels.yaml", help="Path to detector_labels.yaml")
    parser.add_argument("--images-info", type=str, default=None, help="Path to JSON file containing image metadata (required for yolo2coco)")

    args = parser.parse_args()

    try:
        if args.mode == "coco2yolo":
            output_files = coco_to_yolo(
                coco_json_path=Path(args.input),
                output_yolo_dir=Path(args.output),
                label_config_path=Path(args.labels_config),
            )
            print(f"Successfully converted COCO JSON to {len(output_files)} YOLO txt files in {args.output}")

        elif args.mode == "yolo2coco":
            if not args.images_info:
                print("Error: --images-info JSON file is required for yolo2coco mode.")
                sys.exit(1)

            with open(args.images_info, "r") as f:
                images_meta = json.load(f)

            out_path = yolo_to_coco(
                yolo_dir=Path(args.input),
                images_info=images_meta,
                output_coco_path=Path(args.output),
                label_config_path=Path(args.labels_config),
            )
            print(f"Successfully converted YOLO txt files to COCO JSON at {out_path}")

    except Exception as e:
        logging.error(f"Annotation conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
