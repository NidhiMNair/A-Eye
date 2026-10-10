"""Tests for Track2Pipeline orchestrator:
- End-to-end execution from FrameBatch -> Track2Result
- Multi-frame batch processing
- Error handling (type checking, error propagation)
- Context reset functionality
- Custom VLM injection
"""

import pytest
from track2.models import (
    Frame,
    FrameBatch,
    Track2Result,
    PerceptionResult,
    DetectedObject,
    BoundingBox,
    AssistanceCategory,
)
from track2.pipeline import Track2Pipeline
from track2.vlm import MockVLM, VisionLanguageModel, GeminiVLMError


def test_pipeline_default_mock_e2e():
    """Verify default pipeline runs end-to-end offline using MockVLM."""
    pipeline = Track2Pipeline()
    assert isinstance(pipeline.vlm, MockVLM)

    frame = Frame(
        frame_id="cam_001",
        timestamp_ms=1710000000000,
        image_data=b"\x89PNG\r\n\x1a\nfakeimagebytes",
    )
    batch = FrameBatch(frames=[frame])

    result = pipeline.process(batch)

    # 1. Verify result type and top-level fields
    assert isinstance(result, Track2Result)
    assert result.frame_id == "cam_001"
    assert result.timestamp_ms == 1710000000000
    assert isinstance(result.summary, str)
    assert len(result.summary) > 0

    # 2. Verify all reasoning stages are present and validated
    assert result.perception is not None
    assert result.spatial is not None
    assert result.context is not None
    assert result.decision is not None

    # MockVLM detects person and chair
    labels = [obj.label for obj in result.perception.objects]
    assert "person" in labels
    assert "chair" in labels

    # Spatial analysis verified
    assert len(result.spatial.objects) == len(result.perception.objects)
    
    # Decision verified
    assert result.decision.category in list(AssistanceCategory)


def test_pipeline_multi_frame_batch():
    """Verify processing batches with multiple frames."""
    pipeline = Track2Pipeline()

    frame1 = Frame(
        frame_id="cam_001",
        timestamp_ms=1000,
        image_data=b"\x89PNG\r\n\x1a\nframe1",
    )
    frame2 = Frame(
        frame_id="cam_002",
        timestamp_ms=2000,
        image_data=b"\x89PNG\r\n\x1a\nframe2",
    )
    batch = FrameBatch(frames=[frame1, frame2])

    result = pipeline.process(batch)
    assert result.frame_id == "cam_002"
    assert result.context.is_multi_frame is True
    assert result.context.frame_count >= 2


def test_pipeline_rejects_invalid_inputs():
    """Verify input validation rejects non-FrameBatch objects."""
    pipeline = Track2Pipeline()

    with pytest.raises(TypeError, match="Track2Pipeline expects a FrameBatch"):
        pipeline.process("not a batch")  # type: ignore

    with pytest.raises(TypeError, match="Track2Pipeline expects a FrameBatch"):
        pipeline.process(None)  # type: ignore


def test_pipeline_context_reset():
    """Verify resetting context clears temporal tracking history."""
    pipeline = Track2Pipeline()

    frame = Frame(
        frame_id="cam_001",
        timestamp_ms=1000,
        image_data=b"\x89PNG\r\n\x1a\nframe1",
    )
    batch = FrameBatch(frames=[frame])

    # First run
    res1 = pipeline.process(batch)
    assert "person" in res1.context.new_objects

    # Second run without reset: person should be persistent
    res2 = pipeline.process(batch)
    assert "person" in res2.context.persistent_objects

    # Reset context
    pipeline.reset_context()

    # Third run after reset: person should again be newly observed baseline
    res3 = pipeline.process(batch)
    assert "person" in res3.context.new_objects
    assert res3.context.persistent_objects == []


def test_pipeline_vlm_error_propagation():
    """Verify that errors raised by VLM are propagated and never fabricate data."""
    class FailingVLM(VisionLanguageModel):
        def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
            raise GeminiVLMError("Simulated upstream VLM service outage")

    pipeline = Track2Pipeline(vlm=FailingVLM())

    frame = Frame(
        frame_id="cam_001",
        timestamp_ms=1000,
        image_data=b"\x89PNG\r\n\x1a\nframe1",
    )
    batch = FrameBatch(frames=[frame])

    with pytest.raises(GeminiVLMError, match="Simulated upstream VLM service outage"):
        pipeline.process(batch)


def test_pipeline_custom_vlm_injection():
    """Verify custom VisionLanguageModel injection works seamlessly."""
    class CustomVLM(VisionLanguageModel):
        def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
            return PerceptionResult(
                frame_id=frame_batch.frames[0].frame_id,
                timestamp_ms=frame_batch.frames[0].timestamp_ms,
                scene_description="Custom test room",
                scene_label="test_room",
                objects=[
                    DetectedObject(
                        label="robot",
                        conf=0.99,
                        bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.6, y_max=0.6),
                    )
                ],
                hazards=["robot"],
            )

    pipeline = Track2Pipeline(vlm=CustomVLM())
    frame = Frame(
        frame_id="custom_01",
        timestamp_ms=5000,
        image_data=b"testbytes",
    )
    result = pipeline.process(FrameBatch(frames=[frame]))

    assert result.perception.scene_label == "test_room"
    assert result.decision.category == AssistanceCategory.ALERT
    assert any(item.item == "robot" for item in result.decision.relevant_items)
