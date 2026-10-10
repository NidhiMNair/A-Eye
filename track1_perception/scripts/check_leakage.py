"""
Standalone CLI tool to verify zero session and frame leakage across dataset manifests.

Usage:
  python scripts/check_leakage.py --splits-dir data/splits
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.data.splits import check_leakage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Standalone zero-leakage checker for split manifests.")
    parser.add_argument("--splits-dir", type=str, default="data/splits", help="Directory containing split manifests")

    args = parser.parse_args()

    splits_dir = Path(args.splits_dir)
    manifests = {
        "train": splits_dir / "train_manifest.csv",
        "val": splits_dir / "val_manifest.csv",
        "test": splits_dir / "test_manifest.csv",
    }

    try:
        check_leakage(manifests)
        print("PASS: Zero session or frame path leakage detected across splits.")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: Leakage check failed!\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
