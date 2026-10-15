"""Complete Offline Functional Test Suite for Track 2 Pipeline.

Tests all mock scenarios (A-H), edge cases, and Track 2 -> Track 3 boundary
without requiring an internet connection or Gemini API key.
"""

from __future__ import annotations

import json
import pytest

from track2.models import (
    AssistanceCategory,
    BoundingBox,
    DetectedObject,
    Frame,
    FrameBatch,
    HorizontalZone,
    PerceptionResult,
    PriorityLevel,
    Track2Result,
    VerticalZone,
)
from track2.pipeline import Track2Pipeline
from track2.vlm import MockVLM, VisionLanguageModel, GeminiVLMError


# Helper for creating minimal test frames
def _make_frame(frame_id: str = "f_01", timestamp_ms: int = 1000) -> Frame:
    return Frame(
        frame_id=frame_id,
        timestamp_ms=timestamp_ms,
        image_data=b"test_image_bytes",
    )


# Custom mock VLM allowing dynamic scenario returns
class ScenarioMockVLM(VisionLanguageModel):
    def __init__(self, perception_responses: list[PerceptionResult]) -> None:
        self._responses = list(perception_responses)
        self._call_count = 0

    def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
        if not isinstance(frame_batch, FrameBatch):
            raise TypeError("FrameBatch expected")
        if len(frame_batch) == 0:
            raise ValueError("FrameBatch cannot be empty")

        if self._call_count < len(self._responses):
            res = self._responses[self._call_count]
            self._call_count += 1
            return res
        # Fallback to last response
        return self._responses[-1]


# ===========================================================================
# 1. SCENARIOS A - F: SINGLE FRAME FUNCTIONAL TESTS
# ===========================================================================

def test_scenario_a_empty_or_no_important_objects():
    """SCENARIO A: Ordinary scene with no hazards and no central obstacles."""
    vlm = MockVLM(
        default_objects=[],
        default_scene_label="empty_hallway",
        default_scene_description="An open, empty hallway with clear visibility.",
        default_hazards=[],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_a")])

    result = pipeline.process(batch)

    # Output verification
    assert isinstance(result, Track2Result)
    assert result.frame_id == "frame_a"
    assert len(result.perception.objects) == 0
    assert len(result.spatial.objects) == 0
    assert len(result.spatial.central_objects) == 0
    assert len(result.perception.hazards) == 0

    # Risk and assistance
    assert result.decision.priority == PriorityLevel.LOW
    assert result.decision.category in (AssistanceCategory.INFO, AssistanceCategory.NONE)
    assert len(result.decision.relevant_items) == 0

    # Verify no fabricated hazards
    assert "hazard" not in result.summary.lower()
    assert "obstacle" not in result.summary.lower()


def test_scenario_b_central_obstacle():
    """SCENARIO B: Obstacle positioned in central camera view."""
    chair_obj = DetectedObject(
        label="chair",
        conf=0.95,
        bbox=BoundingBox(x_min=0.40, y_min=0.40, x_max=0.60, y_max=0.80),
    )
    vlm = MockVLM(
        default_objects=[chair_obj],
        default_scene_label="office_room",
        default_scene_description="Office room with a chair in the central walking path.",
        default_hazards=["chair in walkway"],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_b")])

    result = pipeline.process(batch)

    # Spatial verification
    assert len(result.spatial.objects) == 1
    spatial_obj = result.spatial.objects[0]
    assert spatial_obj.horizontal_zone == HorizontalZone.CENTER
    assert spatial_obj.is_central is True
    assert chair_obj.label in [o.label for o in result.spatial.central_objects]

    # Priority and Assistance verification
    assert result.decision.priority == PriorityLevel.HIGH
    assert result.decision.category == AssistanceCategory.ALERT
    assert any(item.item == "chair" and item.priority == PriorityLevel.HIGH for item in result.decision.relevant_items)
    assert "chair" in result.summary


def test_scenario_c_object_on_left():
    """SCENARIO C: Person/object on the left side with no central obstacle."""
    person_obj = DetectedObject(
        label="person",
        conf=0.90,
        bbox=BoundingBox(x_min=0.05, y_min=0.20, x_max=0.25, y_max=0.80),
    )
    vlm = MockVLM(
        default_objects=[person_obj],
        default_scene_label="hallway",
        default_scene_description="Hallway with a person standing on the left.",
        default_hazards=[],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_c")])

    result = pipeline.process(batch)

    # Spatial verification
    spatial_obj = result.spatial.objects[0]
    assert spatial_obj.horizontal_zone == HorizontalZone.LEFT
    assert spatial_obj.is_central is False
    assert len(result.spatial.central_objects) == 0

    # Result should NOT classify as an emergency alert
    assert result.decision.category != AssistanceCategory.ALERT
    assert result.decision.priority in (PriorityLevel.LOW, PriorityLevel.MEDIUM)


def test_scenario_d_object_on_right():
    """SCENARIO D: Relevant object on the right side."""
    pillar_obj = DetectedObject(
        label="pillar",
        conf=0.88,
        bbox=BoundingBox(x_min=0.75, y_min=0.10, x_max=0.95, y_max=0.90),
    )
    vlm = MockVLM(
        default_objects=[pillar_obj],
        default_scene_label="atrium",
        default_scene_description="Atrium with an architectural pillar on the right.",
        default_hazards=[],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_d")])

    result = pipeline.process(batch)

    # Spatial verification
    spatial_obj = result.spatial.objects[0]
    assert spatial_obj.horizontal_zone == HorizontalZone.RIGHT
    assert spatial_obj.is_central is False
    assert len(result.spatial.central_objects) == 0
    assert result.decision.category in (AssistanceCategory.GUIDANCE, AssistanceCategory.INFO)


def test_scenario_e_multiple_objects_preserve_spatial_integrity():
    """SCENARIO E: Multiple objects (left, center, right) retain their respective coordinates."""
    door_obj = DetectedObject(
        label="door",
        conf=0.92,
        bbox=BoundingBox(x_min=0.05, y_min=0.10, x_max=0.25, y_max=0.80),  # LEFT
    )
    cone_obj = DetectedObject(
        label="traffic_cone",
        conf=0.95,
        bbox=BoundingBox(x_min=0.45, y_min=0.50, x_max=0.55, y_max=0.80),  # CENTER
    )
    plant_obj = DetectedObject(
        label="plant",
        conf=0.85,
        bbox=BoundingBox(x_min=0.75, y_min=0.30, x_max=0.95, y_max=0.70),  # RIGHT
    )
    vlm = MockVLM(
        default_objects=[door_obj, cone_obj, plant_obj],
        default_scene_label="entrance_hall",
        default_scene_description="Entrance hall with a door on the left, a cone ahead, and a plant on the right.",
        default_hazards=["traffic_cone"],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_e")])

    result = pipeline.process(batch)

    assert len(result.spatial.objects) == 3

    door_info = next(o for o in result.spatial.objects if o.label == "door")
    cone_info = next(o for o in result.spatial.objects if o.label == "traffic_cone")
    plant_info = next(o for o in result.spatial.objects if o.label == "plant")

    # Verify positions are not mixed up
    assert door_info.horizontal_zone == HorizontalZone.LEFT
    assert cone_info.horizontal_zone == HorizontalZone.CENTER
    assert plant_info.horizontal_zone == HorizontalZone.RIGHT

    assert cone_info.is_central is True
    assert door_info.is_central is False
    assert plant_info.is_central is False

    # Relative positions check
    assert any("left of traffic_cone" in r for r in door_info.relative_positions)
    assert any("right of traffic_cone" in r for r in plant_info.relative_positions)


def test_scenario_f_potential_hazard():
    """SCENARIO F: Explicit hazard reported in perception result."""
    spill_obj = DetectedObject(
        label="liquid_spill",
        conf=0.90,
        bbox=BoundingBox(x_min=0.30, y_min=0.60, x_max=0.70, y_max=0.90),
    )
    vlm = MockVLM(
        default_objects=[spill_obj],
        default_scene_label="hallway",
        default_scene_description="Slippery floor with a visible liquid spill in pathway.",
        default_hazards=["liquid_spill"],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    batch = FrameBatch(frames=[_make_frame("frame_f")])

    result = pipeline.process(batch)

    # Risk and assistance
    assert result.decision.priority == PriorityLevel.HIGH
    assert result.decision.category == AssistanceCategory.ALERT
    assert any(item.item == "liquid_spill" and item.is_hazard for item in result.decision.relevant_items)

    # Conservative output verification: no physical distance or safety claims
    summary_lower = result.summary.lower()
    assert "safe" not in summary_lower
    assert "meters" not in summary_lower
    assert "feet" not in summary_lower


# ===========================================================================
# 2. SCENARIOS G & H: TEMPORAL PERSISTENCE & CHANGE REASONING
# ===========================================================================

def test_scenario_g_multi_frame_persistence():
    """SCENARIO G: Consecutive observations of a central obstacle persist across frames."""
    # Central obstacle
    obstacle = DetectedObject(
        label="barrier",
        conf=0.94,
        bbox=BoundingBox(x_min=0.40, y_min=0.40, x_max=0.60, y_max=0.80),
    )

    p1 = PerceptionResult(
        frame_id="f_01",
        timestamp_ms=1000,
        scene_description="Corridor with barrier ahead.",
        scene_label="corridor",
        objects=[obstacle],
        hazards=["barrier"],
    )
    p2 = PerceptionResult(
        frame_id="f_02",
        timestamp_ms=1500,
        scene_description="Corridor with barrier ahead.",
        scene_label="corridor",
        objects=[obstacle],
        hazards=["barrier"],
    )
    p3 = PerceptionResult(
        frame_id="f_03",
        timestamp_ms=2000,
        scene_description="Corridor with barrier ahead.",
        scene_label="corridor",
        objects=[obstacle],
        hazards=["barrier"],
    )

    pipeline = Track2Pipeline(vlm=ScenarioMockVLM([p1, p2, p3]))

    # Frame 1: Initial baseline
    r1 = pipeline.process(FrameBatch(frames=[_make_frame("f_01", 1000)]))
    assert r1.context.new_objects == ["barrier"]
    assert r1.context.persistent_objects == []

    # Frame 2: Barrier persists
    r2 = pipeline.process(FrameBatch(frames=[_make_frame("f_02", 1500)]))
    assert "barrier" in r2.context.persistent_objects
    assert "barrier" in r2.context.central_persistence
    assert r2.context.new_objects == []

    # Frame 3: Barrier continues to persist
    r3 = pipeline.process(FrameBatch(frames=[_make_frame("f_03", 2000)]))
    assert "barrier" in r3.context.persistent_objects
    assert "barrier" in r3.context.central_persistence
    assert r3.decision.category == AssistanceCategory.ALERT


def test_scenario_h_changed_observation():
    """SCENARIO H: Object changes between consecutive frames."""
    chair_obj = DetectedObject(
        label="chair",
        conf=0.90,
        bbox=BoundingBox(x_min=0.40, y_min=0.40, x_max=0.60, y_max=0.80),
    )
    table_obj = DetectedObject(
        label="table",
        conf=0.88,
        bbox=BoundingBox(x_min=0.70, y_min=0.30, x_max=0.95, y_max=0.70),
    )

    p1 = PerceptionResult(
        frame_id="f_01",
        timestamp_ms=1000,
        scene_description="Room with chair in center.",
        scene_label="room",
        objects=[chair_obj],
    )
    p2 = PerceptionResult(
        frame_id="f_02",
        timestamp_ms=1500,
        scene_description="Room with table on right, chair gone.",
        scene_label="room",
        objects=[table_obj],
    )

    pipeline = Track2Pipeline(vlm=ScenarioMockVLM([p1, p2]))

    # Frame 1
    r1 = pipeline.process(FrameBatch(frames=[_make_frame("f_01", 1000)]))
    assert r1.context.new_objects == ["chair"]

    # Frame 2: Chair disappeared, table appeared
    r2 = pipeline.process(FrameBatch(frames=[_make_frame("f_02", 1500)]))
    assert "chair" not in r2.context.persistent_objects
    assert r2.context.new_objects == ["table"]
    assert any("Newly observed in scene: table" in ch for ch in r2.context.changes)


# ===========================================================================
# 3. EDGE CASES & ERROR HANDLING
# ===========================================================================

def test_edge_case_empty_framebatch():
    """Edge Case: FrameBatch with 0 frames raises ValueError."""
    pipeline = Track2Pipeline()
    with pytest.raises(ValueError, match="at least one Frame|cannot be empty"):
        pipeline.process(FrameBatch(frames=[]))


def test_edge_case_invalid_bounding_box_coordinates():
    """Edge Case: BoundingBox validates min < max and bounds in [0.0, 1.0]."""
    # x_min > x_max
    with pytest.raises(ValueError):
        BoundingBox(x_min=0.8, y_min=0.1, x_max=0.2, y_max=0.9)

    # y_min > y_max
    with pytest.raises(ValueError):
        BoundingBox(x_min=0.1, y_min=0.9, x_max=0.8, y_max=0.2)

    # Out of bounds (< 0.0)
    with pytest.raises(ValueError):
        BoundingBox(x_min=-0.1, y_min=0.1, x_max=0.5, y_max=0.5)

    # Out of bounds (> 1.0)
    with pytest.raises(ValueError):
        BoundingBox(x_min=0.1, y_min=0.1, x_max=1.5, y_max=0.5)


def test_edge_case_single_object_relative_positions():
    """Edge Case: Single object has no relative positions or overlaps."""
    vlm = MockVLM(
        default_objects=[
            DetectedObject(
                label="lone_chair",
                conf=0.9,
                bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.6, y_max=0.6),
            )
        ]
    )
    pipeline = Track2Pipeline(vlm=vlm)
    res = pipeline.process(FrameBatch(frames=[_make_frame()]))

    assert len(res.spatial.objects) == 1
    assert res.spatial.objects[0].relative_positions == []
    assert res.spatial.objects[0].overlapping_labels == []


def test_edge_case_many_objects():
    """Edge Case: Scene with 20 objects processes accurately without index errors."""
    many_objects = [
        DetectedObject(
            label=f"item_{i}",
            conf=0.8,
            bbox=BoundingBox(
                x_min=round((i % 5) * 0.18 + 0.01, 3),
                y_min=round((i // 5) * 0.22 + 0.01, 3),
                x_max=round((i % 5) * 0.18 + 0.15, 3),
                y_max=round((i // 5) * 0.22 + 0.18, 3),
            ),
        )
        for i in range(20)
    ]
    vlm = MockVLM(default_objects=many_objects, default_scene_label="crowded_shelf")
    pipeline = Track2Pipeline(vlm=vlm)
    res = pipeline.process(FrameBatch(frames=[_make_frame()]))

    assert len(res.spatial.objects) == 20
    assert len(res.perception.objects) == 20
    assert res.decision is not None


def test_edge_case_no_hazards_vs_multiple_hazards():
    """Edge Case: Clean handling of multiple distinct hazards."""
    vlm = MockVLM(
        default_objects=[
            DetectedObject(label="broken_glass", conf=0.9, bbox=BoundingBox(x_min=0.1, y_min=0.7, x_max=0.3, y_max=0.9)),
            DetectedObject(label="open_pit", conf=0.95, bbox=BoundingBox(x_min=0.4, y_min=0.6, x_max=0.6, y_max=0.9)),
        ],
        default_hazards=["broken_glass", "open_pit", "low_hanging_wire"],
    )
    pipeline = Track2Pipeline(vlm=vlm)
    res = pipeline.process(FrameBatch(frames=[_make_frame()]))

    assert res.decision.category == AssistanceCategory.ALERT
    assert res.decision.priority == PriorityLevel.HIGH
    hazard_items = [i.item for i in res.decision.relevant_items if i.is_hazard]
    assert "broken_glass" in hazard_items
    assert "open_pit" in hazard_items
    assert "low_hanging_wire" in hazard_items


def test_edge_case_uncertain_observation_propagates():
    """Edge Case: Uncertainties reported by VLM are preserved in spatial and pipeline results."""
    p = PerceptionResult(
        frame_id="f_uncertain",
        timestamp_ms=1000,
        scene_description="Dimly lit corridor.",
        scene_label="corridor",
        objects=[
            DetectedObject(
                label="unknown_shape",
                conf=0.35,  # Low confidence
                bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.6, y_max=0.6),
            )
        ],
        uncertainties=["Heavy shadows cast across frame", "Low lighting conditions"],
    )
    pipeline = Track2Pipeline(vlm=ScenarioMockVLM([p]))
    res = pipeline.process(FrameBatch(frames=[_make_frame("f_uncertain")]))

    assert "Heavy shadows cast across frame" in res.spatial.uncertainties
    assert "Low lighting conditions" in res.spatial.uncertainties


def test_edge_case_vlm_failure_propagates_without_fabrication():
    """Edge Case: When VLM fails, pipeline raises exception and never fabricates false detections."""
    class FailingVLM(VisionLanguageModel):
        def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
            raise GeminiVLMError("Simulated upstream VLM failure")

    pipeline = Track2Pipeline(vlm=FailingVLM())
    with pytest.raises(GeminiVLMError, match="Simulated upstream VLM failure"):
        pipeline.process(FrameBatch(frames=[_make_frame()]))


# ===========================================================================
# 4. TRACK 2 -> TRACK 3 BOUNDARY INTEGRATION
# ===========================================================================

def test_track2_to_track3_structured_contract_boundary():
    """
    Verify Track 2 delivers a completely structured, machine-readable contract
    that Track 3 can inspect and consume cleanly without parsing unstructured text.
    """
    pipeline = Track2Pipeline()
    batch = FrameBatch(frames=[_make_frame("boundary_01", 1710000000000)])

    result = pipeline.process(batch)

    # 1. Type contract verification
    assert isinstance(result, Track2Result)
    assert isinstance(result.decision.category, AssistanceCategory)
    assert isinstance(result.decision.priority, PriorityLevel)
    assert isinstance(result.decision.relevant_items, list)

    # 2. JSON Serialization (Track 3 inter-process or network communication)
    json_str = result.model_dump_json()
    assert isinstance(json_str, str)
    data = json.loads(json_str)

    assert data["frame_id"] == "boundary_01"
    assert data["timestamp_ms"] == 1710000000000
    assert "decision" in data
    assert "category" in data["decision"]
    assert "priority" in data["decision"]
    assert "perception" in data
    assert "spatial" in data
    assert "context" in data

    # 3. Verify no audio bytes, UI widgets, or raw provider handles leaked
    assert not hasattr(result, "audio_stream")
    assert not hasattr(result, "ui_component")
    assert not hasattr(result, "gemini_client")
