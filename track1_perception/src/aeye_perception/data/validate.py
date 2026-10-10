"""
Dataset validation and integrity auditing tool.

Scans frame images and annotation files to report syntax errors, out-of-bounds boxes,
unmapped class IDs, orphaned files, empty annotations, duplicate frames, and class counts.
"""

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Dict, List, Set, Union, Optional
import yaml
from PIL import Image

from aeye_perception.data.converters import load_class_labels

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    class_counts: Dict[str, int] = field(default_factory=dict)
    total_images: int = 0
    total_labels: int = 0
    empty_label_files: int = 0

    def summary_text(self) -> str:
        lines = [
            "=== DATASET VALIDATION REPORT ===",
            f"Status: {'PASSED' if self.is_valid else 'FAILED'}",
            f"Total Images: {self.total_images}",
            f"Total Label Files: {self.total_labels}",
            f"Empty Label Files (Backgrounds): {self.empty_label_files}",
            "\n--- Class Counts ---",
        ]
        for cname, count in sorted(self.class_counts.items()):
            lines.append(f"  - {cname}: {count}")

        if self.warnings:
            lines.append("\n--- WARNINGS ---")
            for w in self.warnings:
                lines.append(f"  [WARN] {w}")

        if self.errors:
            lines.append("\n--- ERRORS ---")
            for e in self.errors:
                lines.append(f"  [ERROR] {e}")

        return "\n".join(lines)


def validate_dataset(
    dataset_dir: Union[str, Path],
    label_config_path: Union[str, Path],
) -> ValidationReport:
    """
    Validate dataset integrity across frames and YOLO annotation files.
    """
    root_dir = Path(dataset_dir)
    report = ValidationReport()

    if not root_dir.exists():
        report.is_valid = False
        report.errors.append(f"Dataset directory does not exist: {root_dir}")
        return report

    class_dict = load_class_labels(label_config_path)

    # Find image and annotation files
    image_extensions = {".jpg", ".jpeg", ".png"}
    images: Dict[str, Path] = {}
    labels: Dict[str, Path] = {}
    seen_frame_paths: Set[str] = set()

    for p in root_dir.rglob("*"):
        if p.is_file():
            if p.suffix.lower() in image_extensions:
                stem = p.stem
                if str(p.resolve()) in seen_frame_paths:
                    report.warnings.append(f"Duplicate frame path detected: {p}")
                seen_frame_paths.add(str(p.resolve()))
                images[stem] = p

            elif p.suffix.lower() == ".txt" and "manifest" not in p.name:
                labels[p.stem] = p

    report.total_images = len(images)
    report.total_labels = len(labels)

    # 1. Images without label files
    missing_labels = set(images.keys()) - set(labels.keys())
    if missing_labels:
        report.warnings.append(f"Found {len(missing_labels)} image(s) without label files.")

    # 2. Labels without image files
    missing_images = set(labels.keys()) - set(images.keys())
    if missing_images:
        report.errors.append(f"Found {len(missing_images)} label file(s) without corresponding image files: {list(missing_images)[:5]}")
        report.is_valid = False

    # 3. Validate label contents & bounding boxes
    for stem, label_path in labels.items():
        with open(label_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            report.empty_label_files += 1
            continue

        for line_num, line in enumerate(lines, 1):
            parts = line.split()
            if len(parts) != 5:
                report.errors.append(
                    f"Malformed line in {label_path.name} (L{line_num}): Expected 5 elements, got {len(parts)} ('{line}')"
                )
                report.is_valid = False
                continue

            try:
                class_id = int(parts[0])
                cx, cy, w, h = [float(val) for val in parts[1:]]
            except ValueError:
                report.errors.append(f"Invalid non-numeric value in {label_path.name} (L{line_num}): '{line}'")
                report.is_valid = False
                continue

            # Check unknown class ID
            if class_id not in class_dict:
                report.errors.append(f"Unknown class ID {class_id} in {label_path.name} (L{line_num}). Allowed: {list(class_dict.keys())}")
                report.is_valid = False
            else:
                class_name = class_dict[class_id]
                report.class_counts[class_name] = report.class_counts.get(class_name, 0) + 1

            # Check box coordinates out of bounds [0.0, 1.0]
            if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0):
                report.errors.append(
                    f"Out of bounds bounding box in {label_path.name} (L{line_num}): cx={cx}, cy={cy}, w={w}, h={h}"
                )
                report.is_valid = False

    logger.info(report.summary_text())
    return report
