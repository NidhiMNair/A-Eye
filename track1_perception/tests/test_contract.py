"""
Unit tests for aeye_perception.contract.

Validates schema constraints, serialization/deserialization, box clamping,
contract versioning, and fixture JSON integrity.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from aeye_perception.contract import (
    PerceptionResult,
    DetectedObject,
    TextBlock,
    MotionVector,
    CONTRACT_VERSION,
)


def test_contract_version_constant():
    """Verify default contract version constant."""
    assert CONTRACT_VERSION == "0.1-draft"


def test_detected_object_bbox_clamping():
    """Verify that bounding box coordinates outside [0, 1] are clamped."""
    obj = DetectedObject(
        label="chair",
        conf=0.9,
        bbox=[-0.2, 0.5, 1.2, 0.8],
    )
    assert obj.bbox == [0.0, 0.5, 1.0, 0.8]


def test_detected_object_bbox_invalid_length():
    """Verify error on bounding box with wrong number of elements."""
    with pytest.raises(ValidationError):
        DetectedObject(
            label="chair",
            conf=0.9,
            bbox=[0.1, 0.2, 0.3],
        )


def test_detected_object_conf_validation():
    """Verify confidence score boundaries."""
    with pytest.raises(ValidationError):
        DetectedObject(label="door", conf=1.5, bbox=[0.1, 0.1, 0.5, 0.5])

    with pytest.raises(ValidationError):
        DetectedObject(label="door", conf=-0.1, bbox=[0.1, 0.1, 0.5, 0.5])


def test_offline_scene_description_must_be_none():
    """Verify that offline source raises error if scene_description is provided."""
    with pytest.raises(ValidationError) as excinfo:
        PerceptionResult(
            frame_id=1,
            timestamp_ms=1000,
            source="offline",
            scene_label="corridor",
            scene_description="A long corridor with chairs",
        )
    assert "scene_description must be None when source is 'offline'" in str(excinfo.value)


def test_online_scene_description_allowed():
    """Verify that online source allows scene_description."""
    res = PerceptionResult(
        frame_id=1,
        timestamp_ms=1000,
        source="online",
        scene_label="corridor",
        scene_description="A long corridor with chairs",
    )
    assert res.scene_description == "A long corridor with chairs"


def test_perception_result_json_roundtrip():
    """Verify JSON serialization and deserialization roundtrip."""
    obj_tracked = DetectedObject(
        label="chair",
        conf=0.85,
        bbox=[0.2, 0.3, 0.5, 0.7],
        track_id=42,
        motion=MotionVector(dx=0.01, dy=-0.02, growth=0.003),
    )
    text_item = TextBlock(
        text="Exit",
        conf=0.95,
        bbox=[0.1, 0.1, 0.3, 0.2],
    )

    result = PerceptionResult(
        frame_id=100,
        timestamp_ms=1700000000000,
        source="offline",
        objects=[obj_tracked],
        text_blocks=[text_item],
        scene_label="corridor",
    )

    json_str = result.to_json()
    reconstructed = PerceptionResult.from_json(json_str)

    assert reconstructed.frame_id == 100
    assert reconstructed.source == "offline"
    assert len(reconstructed.objects) == 1
    assert reconstructed.objects[0].track_id == 42
    assert reconstructed.objects[0].motion.dx == 0.01
    assert reconstructed.text_blocks[0].text == "Exit"
    assert reconstructed.contract_version == CONTRACT_VERSION


def test_empty_objects_and_text_blocks():
    """Verify perception result with empty lists."""
    result = PerceptionResult(
        frame_id=5,
        timestamp_ms=1005,
        source="offline",
    )
    assert result.objects == []
    assert result.text_blocks == []
    assert result.scene_label is None


def test_fixture_file_validation():
    """Verify that committed mock_perception_result.json fixture passes validation."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "mock_perception_result.json"
    assert fixture_path.exists(), f"Fixture file not found at {fixture_path}"

    with open(fixture_path, "r") as f:
        data = json.load(f)

    result = PerceptionResult.model_validate(data)
    assert result.frame_id == 1042
    assert result.source == "offline"
    assert len(result.objects) == 2
    assert result.objects[0].track_id == 12
    assert result.objects[1].track_id is None
    assert len(result.text_blocks) == 1
