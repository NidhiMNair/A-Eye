"""
Unit test suite for WP1.6 Data Tooling.

Tests COCO <-> YOLO roundtrip conversion, frame extraction, session splitting,
reproducibility, zero-leakage assertions, test isolation, and dataset validation.
"""

import csv
import json
from pathlib import Path
import numpy as np
import pytest

from aeye_perception.data.converters import coco_to_yolo, yolo_to_coco
from aeye_perception.data.frame_extraction import extract_frames_from_video
from aeye_perception.data.splits import split_dataset, check_leakage, load_split
from aeye_perception.data.validate import validate_dataset
from scripts.make_synthetic_fixtures import generate_synthetic_clip


@pytest.fixture
def label_config(tmp_path):
    """Create a temporary detector_labels.yaml config."""
    config_path = tmp_path / "detector_labels.yaml"
    content = "classes:\n  0: chair\n  1: table\n  2: door\n"
    config_path.write_text(content)
    return config_path


def test_coco_yolo_roundtrip(tmp_path, label_config):
    """Verify COCO JSON -> YOLO txt -> COCO JSON roundtrip box accuracy."""
    yolo_dir = tmp_path / "yolo_output"
    reconstructed_coco_path = tmp_path / "reconstructed_coco.json"

    # Original COCO JSON structure
    coco_data = {
        "images": [{"id": 1, "file_name": "frame_0001.jpg", "width": 640, "height": 480}],
        "annotations": [
            {
                "id": 101,
                "image_id": 1,
                "category_id": 0,
                "bbox": [64.0, 48.0, 320.0, 240.0],  # [x_min, y_min, w, h]
                "area": 76800.0,
                "iscrowd": 0,
            }
        ],
        "categories": [{"id": 0, "name": "chair", "supercategory": "obstacle"}],
    }

    coco_json_path = tmp_path / "original_coco.json"
    coco_json_path.write_text(json.dumps(coco_data, indent=2))

    # 1. Convert COCO to YOLO
    txt_files = coco_to_yolo(coco_json_path, yolo_dir, label_config)
    assert len(txt_files) == 1
    assert txt_files[0].name == "frame_0001.txt"

    # 2. Convert YOLO back to COCO
    yolo_to_coco(yolo_dir, coco_data["images"], reconstructed_coco_path, label_config)
    assert reconstructed_coco_path.exists()

    with open(reconstructed_coco_path, "r") as f:
        recon_data = json.load(f)

    assert len(recon_data["annotations"]) == 1
    orig_box = coco_data["annotations"][0]["bbox"]
    recon_box = recon_data["annotations"][0]["bbox"]

    # Assert coordinates match within 1 pixel tolerance
    for orig_val, recon_val in zip(orig_box, recon_box):
        assert abs(orig_val - recon_val) <= 1.0


def test_frame_extraction_on_synthetic_video(tmp_path):
    """Verify frame extraction and manifest creation from synthetic clip."""
    video_dir = tmp_path / "synthetic_input"
    output_dir = tmp_path / "extracted_session"

    clip_path = generate_synthetic_clip(video_dir, num_frames=20, fps=10)
    manifest_path = extract_frames_from_video(
        video_path=clip_path,
        output_dir=output_dir,
        session_id="20261012_corridorA_01",
        target_fps=2.0,
    )

    assert manifest_path.exists()
    assert (output_dir / "frames").exists()

    with open(manifest_path, "r") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) > 0
    assert rows[0]["session_id"] == "20261012_corridorA_01"
    assert "timestamp_ms" in rows[0]


def test_leakage_check_valid_and_leaky(tmp_path):
    """Verify that valid splits pass leakage check and leaky splits raise error."""
    m_train = tmp_path / "train_manifest.csv"
    m_val = tmp_path / "val_manifest.csv"
    m_test = tmp_path / "test_manifest.csv"

    # Valid non-overlapping manifests
    m_train.write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locA_01,frame_0.jpg,0,0\n")
    m_val.write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locB_02,frame_1.jpg,0,0\n")
    m_test.write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locC_03,frame_2.jpg,0,0\n")

    manifests = {"train": m_train, "val": m_val, "test": m_test}
    assert check_leakage(manifests) is True

    # Intentionally leaky manifest (session_01 appears in both train and val)
    m_val_leaky = tmp_path / "val_leaky_manifest.csv"
    m_val_leaky.write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locA_01,frame_99.jpg,0,0\n")
    leaky_manifests = {"train": m_train, "val": m_val_leaky, "test": m_test}

    with pytest.raises(ValueError) as excinfo:
        check_leakage(leaky_manifests)
    assert "DATA LEAKAGE DETECTED" in str(excinfo.value)


def test_split_dataset_and_reproducibility(tmp_path, label_config):
    """Verify session-based splitting reproducibility and seed behavior."""
    sessions = [
        {"session_id": f"20261012_loc_{i:02d}", "manifest_rows": [{"session_id": f"20261012_loc_{i:02d}", "frame_path": f"f_{i}.jpg", "frame_index": 0, "timestamp_ms": 0}]}
        for i in range(10)
    ]

    out_1 = tmp_path / "split_run_1"
    out_2 = tmp_path / "split_run_2"
    out_diff = tmp_path / "split_run_diff"

    # Run 1 with seed 42
    split_dataset(sessions, out_1, seed=42, label_config_path=label_config)
    # Run 2 with same seed 42
    split_dataset(sessions, out_2, seed=42, label_config_path=label_config)
    # Run 3 with different seed 99
    split_dataset(sessions, out_diff, seed=99, label_config_path=label_config)

    t1 = (out_1 / "train_manifest.csv").read_text()
    t2 = (out_2 / "train_manifest.csv").read_text()
    td = (out_diff / "train_manifest.csv").read_text()

    assert t1 == t2, "Same seed must produce identical splits"
    assert t1 != td, "Different seed must produce different split distribution"


def test_test_set_protection(tmp_path):
    """Verify load_split protection mechanism for test split."""
    splits_dir = tmp_path / "splits"
    splits_dir.mkdir()
    (splits_dir / "test_manifest.csv").write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locA_01,f.jpg,0,0\n")
    (splits_dir / "train_manifest.csv").write_text("session_id,frame_path,frame_index,timestamp_ms\n20261012_locB_02,f2.jpg,0,0\n")

    # Train split loads normally
    train_rows = load_split("train", splits_dir)
    assert len(train_rows) == 1

    # Test split without allow_test flag MUST raise PermissionError
    with pytest.raises(PermissionError):
        load_split("test", splits_dir, allow_test=False)

    # Test split with allow_test=True succeeds
    test_rows = load_split("test", splits_dir, allow_test=True)
    assert len(test_rows) == 1


def test_dataset_validator_error_detection(tmp_path, label_config):
    """Verify validator catches out-of-range boxes, missing files, unknown class IDs."""
    data_dir = tmp_path / "dataset"
    data_dir.mkdir()

    # Image without label
    (data_dir / "frame_001.jpg").write_text("fake image content")

    # Label without image
    (data_dir / "frame_002.txt").write_text("0 0.5 0.5 0.2 0.2\n")

    # Malformed label / out of bounds box
    (data_dir / "frame_003.jpg").write_text("fake image")
    (data_dir / "frame_003.txt").write_text("999 1.5 0.5 0.2 0.2\n")  # Unknown class 999 & cx=1.5 out of bounds

    report = validate_dataset(data_dir, label_config)

    assert report.is_valid is False
    assert len(report.errors) > 0

    # Verify specific error messages captured
    err_str = " ".join(report.errors)
    assert "without corresponding image" in err_str
    assert "Unknown class ID 999" in err_str
    assert "Out of bounds" in err_str
