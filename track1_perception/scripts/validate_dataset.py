"""
CLI entry point for dataset validation and health auditing.

Usage:
  python scripts/validate_dataset.py --data-dir data/raw --labels-config configs/detector_labels.yaml
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.data.validate import validate_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Audit dataset health, bounding boxes, labels, and file syntax.")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Path to dataset raw directory")
    parser.add_argument("--labels-config", type=str, default="configs/detector_labels.yaml", help="Path to detector_labels.yaml")

    args = parser.parse_args()

    report = validate_dataset(
        dataset_dir=Path(args.data_dir),
        label_config_path=Path(args.labels_config),
    )

    print(report.summary_text())

    if not report.is_valid:
        print("\nRESULT: FAILED - Dataset integrity errors detected!")
        sys.exit(1)
    else:
        print("\nRESULT: PASSED - Dataset is clean and valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
