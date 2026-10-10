"""
Unit tests for aeye_perception.geometry utilities.
"""

import pytest
from aeye_perception.geometry import (
    normalize_bbox,
    denormalize_bbox,
    clamp_bbox,
    validate_bbox,
    compute_center,
    compute_area,
    compute_iou,
)


def test_normalize_and_denormalize():
    """Test roundtrip conversion between pixel and normalized coordinates."""
    img_w, img_h = 640, 480
    pixel_box = [64, 48, 320, 240]

    norm = normalize_bbox(pixel_box, img_w, img_h)
    assert norm == [0.1, 0.1, 0.5, 0.5]

    denorm = denormalize_bbox(norm, img_w, img_h)
    assert denorm == pixel_box


def test_clamp_bbox_out_of_bounds():
    """Test clamping out of bound box values."""
    raw = [-0.1, -0.5, 1.5, 2.0]
    clamped = clamp_bbox(raw)
    assert clamped == [0.0, 0.0, 1.0, 1.0]


def test_clamp_bbox_reversed_coords():
    """Test clamping handles x1 > x2 or y1 > y2."""
    raw = [0.8, 0.9, 0.2, 0.3]
    clamped = clamp_bbox(raw)
    assert clamped == [0.2, 0.3, 0.8, 0.9]


def test_validate_bbox():
    """Test bbox validity checker."""
    assert validate_bbox([0.1, 0.2, 0.5, 0.6]) is True
    assert validate_bbox([0.5, 0.2, 0.1, 0.6]) is False  # x1 > x2
    assert validate_bbox([0.1, 0.2, 0.5]) is False       # length != 4
    assert validate_bbox([-0.1, 0.2, 0.5, 0.6]) is False # negative value


def test_compute_center():
    """Test bounding box center computation."""
    bbox = [0.1, 0.2, 0.5, 0.6]
    cx, cy = compute_center(bbox)
    assert cx == 0.3
    assert cy == 0.4


def test_compute_area():
    """Test bounding box area calculation."""
    bbox = [0.1, 0.2, 0.5, 0.6]
    area = compute_area(bbox)
    # width = 0.4, height = 0.4 -> area = 0.16
    assert abs(area - 0.16) < 1e-4


def test_compute_iou_identical():
    """Test IoU of identical bounding boxes is 1.0."""
    b1 = [0.1, 0.1, 0.5, 0.5]
    b2 = [0.1, 0.1, 0.5, 0.5]
    assert compute_iou(b1, b2) == 1.0


def test_compute_iou_disjoint():
    """Test IoU of non-overlapping boxes is 0.0."""
    b1 = [0.0, 0.0, 0.2, 0.2]
    b2 = [0.5, 0.5, 0.8, 0.8]
    assert compute_iou(b1, b2) == 0.0


def test_compute_iou_partial():
    """Test IoU of partially overlapping boxes."""
    b1 = [0.0, 0.0, 0.4, 0.4]  # area = 0.16
    b2 = [0.2, 0.2, 0.6, 0.6]  # area = 0.16
    # Intersection: [0.2, 0.2, 0.4, 0.4] -> area = 0.04
    # Union: 0.16 + 0.16 - 0.04 = 0.28
    # IoU: 0.04 / 0.28 = 1/7 ~= 0.1429
    iou = compute_iou(b1, b2)
    assert abs(iou - 0.1429) < 1e-3
