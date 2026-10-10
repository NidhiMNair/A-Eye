"""
CLI entry point for session-based dataset splitting and zero-leakage validation.

Usage:
  python scripts/split_dataset.py --data-dir data/raw --output-dir data/splits --seed 42
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aeye_perception.data.splits import split_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def discover_sessions(raw_dir: Path) -> List[Dict[str, Any]]:
    """Scan raw directory to collect session metadata and manifest rows."""
    sessions = []
    if not raw_dir.exists():
        return sessions

    for session_folder in sorted(raw_dir.iterdir()):
        if session_folder.is_dir():
            manifest_file = session_folder / "manifest.csv"
            rows = []
            if manifest_file.exists():
                with open(manifest_file, "r", newline="") as f:
                    reader = csv.DictReader(f)
                    rows = [dict(r) for r in reader]

            sessions.append({
                "session_id": session_folder.name,
                "manifest_rows": rows,
                "folder_path": str(session_folder),
            })

    return sessions


def main():
    parser = argparse.ArgumentParser(description="Split dataset by session into train/val/test splits.")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Path to raw session recordings directory")
    parser.add_argument("--output-dir", type=str, default="data/splits", help="Output directory for split manifests")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Train split ratio (default: 0.70)")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Val split ratio (default: 0.15)")
    parser.add_argument("--test-ratio", type=float, default=0.15, help="Test split ratio (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split reproducibility")
    parser.add_argument("--stratify", action="store_true", help="Enable best-effort class stratification")
    parser.add_argument("--labels-config", type=str, default="configs/detector_labels.yaml", help="Path to detector_labels.yaml")

    args = parser.parse_args()

    raw_path = Path(args.data_dir)
    sessions = discover_sessions(raw_path)

    if not sessions:
        print(f"Error: No sessions discovered in {raw_path}")
        sys.exit(1)

    try:
        manifest_paths = split_dataset(
            sessions=sessions,
            output_dir=Path(args.output_dir),
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
            seed=args.seed,
            stratify=args.stratify,
            label_config_path=Path(args.labels_config),
        )
        print("Dataset splitting completed successfully with ZERO LEAKAGE verified!")
        for split, path in manifest_paths.items():
            print(f"  - {split}: {path}")

    except Exception as e:
        logging.error(f"Dataset splitting failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
