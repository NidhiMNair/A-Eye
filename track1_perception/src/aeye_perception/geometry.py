"""
Bounding box geometry utilities for normalized image coordinates.

All normalized bounding boxes are represented as [x1, y1, x2, y2]:
- Range: [0.0, 1.0]
- Origin: top-left corner
- x axis: rightward
- y axis: downward
"""

from typing import Tuple, List
import numpy as np


def normalize_bbox(bbox_px: List[float], img_width: int, img_height: int) -> List[float]:
    """
    Convert absolute pixel bounding box [x1_px, y1_px, x2_px, y2_px] to normalized [0.0, 1.0].
    """
    if img_width <= 0 or img_height <= 0:
        raise ValueError(f"Image dimensions must be positive, got width={img_width}, height={img_height}")
    x1, y1, x2, y2 = bbox_px
    norm_bbox = [
        x1 / img_width,
        y1 / img_height,
        x2 / img_width,
        y2 / img_height,
    ]
    return clamp_bbox(norm_bbox)


def denormalize_bbox(bbox_norm: List[float], img_width: int, img_height: int) -> List[int]:
    """
    Convert normalized bounding box [x1, y1, x2, y2] to absolute pixel coordinates [x1_px, y1_px, x2_px, y2_px].
    """
    clamped = clamp_bbox(bbox_norm)
    x1, y1, x2, y2 = clamped
    return [
        int(round(x1 * img_width)),
        int(round(y1 * img_height)),
        int(round(x2 * img_width)),
        int(round(y2 * img_height)),
    ]


def clamp_bbox(bbox: List[float]) -> List[float]:
    """
    Clamp bounding box coordinates to [0.0, 1.0] and ensure x1 <= x2, y1 <= y2.
    """
    if len(bbox) != 4:
        raise ValueError(f"Expected 4 bounding box elements, got {len(bbox)}")
    x1, y1, x2, y2 = [max(0.0, min(1.0, float(v))) for v in bbox]
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    return [round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)]


def validate_bbox(bbox: List[float]) -> bool:
    """
    Check if a bounding box is valid [x1, y1, x2, y2] within range [0.0, 1.0] and non-empty.
    """
    if len(bbox) != 4:
        return False
    x1, y1, x2, y2 = bbox
    return (0.0 <= x1 <= 1.0 and 0.0 <= y1 <= 1.0 and
            0.0 <= x2 <= 1.0 and 0.0 <= y2 <= 1.0 and
            x1 <= x2 and y1 <= y2)


def compute_center(bbox: List[float]) -> Tuple[float, float]:
    """
    Compute normalized center coordinates (cx, cy) of a bounding box.
    """
    clamped = clamp_bbox(bbox)
    cx = (clamped[0] + clamped[2]) / 2.0
    cy = (clamped[1] + clamped[3]) / 2.0
    return round(cx, 4), round(cy, 4)


def compute_area(bbox: List[float]) -> float:
    """
    Compute normalized area (w * h) of a bounding box.
    """
    clamped = clamp_bbox(bbox)
    width = clamped[2] - clamped[0]
    height = clamped[3] - clamped[1]
    return round(width * height, 6)


def compute_iou(bbox1: List[float], bbox2: List[float]) -> float:
    """
    Compute Intersection over Union (IoU) between two normalized bounding boxes.
    """
    b1 = clamp_bbox(bbox1)
    b2 = clamp_bbox(bbox2)

    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])

    intersection_w = max(0.0, x2 - x1)
    intersection_h = max(0.0, y2 - y1)
    intersection = intersection_w * intersection_h

    area1 = compute_area(b1)
    area2 = compute_area(b2)
    union = area1 + area2 - intersection

    if union <= 0.0:
        return 0.0

    return round(float(intersection / union), 4)
