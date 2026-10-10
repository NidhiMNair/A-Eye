"""
Data management module for A-Eye Track 1 Perception.

Includes frame extraction, annotation conversion, session-based dataset splitting,
leakage checking, test set protection, and integrity validation.
"""

from aeye_perception.data.frame_extraction import extract_frames_from_video
from aeye_perception.data.converters import coco_to_yolo, yolo_to_coco
from aeye_perception.data.splits import split_dataset, check_leakage, load_split
from aeye_perception.data.validate import validate_dataset

__all__ = [
    "extract_frames_from_video",
    "coco_to_yolo",
    "yolo_to_coco",
    "split_dataset",
    "check_leakage",
    "load_split",
    "validate_dataset",
]
