"""Focused tests for Track 2 reasoning components:
- Spatial reasoning (image-space zones, prominence, central view, overlap, relative positions)
- Context reasoning (persistence, new observations, central obstacle persistence)
- Decision reasoning (priority evaluation, assistance categories, alerts, guidance, info, none)
"""

import pytest
from track2.models import (
    BoundingBox,
    DetectedObject,
    HorizontalZone,
    PerceptionResult,
    PriorityLevel,
    AssistanceCategory,
    VerticalZone,
)
from track2.spatial import SpatialReasoner
from track2.context import ContextReasoner
from track2.decision import AssistanceDecisionEngine


# ---------------------------------------------------------------------------
# Spatial Reasoning Tests
# ---------------------------------------------------------------------------

def test_spatial_horizontal_and_vertical_zones():
    reasoner = SpatialReasoner()
    
    # Left, Upper (center at x=0.1, y=0.1)
    left_upper = DetectedObject(
        label="clock",
        conf=0.9,
        bbox=BoundingBox(x_min=0.05, y_min=0.05, x_max=0.15, y_max=0.15),
    )
    # Center, Middle (center at x=0.5, y=0.5)
    center_middle = DetectedObject(
        label="chair",
        conf=0.85,
        bbox=BoundingBox(x_min=0.45, y_min=0.45, x_max=0.55, y_max=0.55),
    )
    # Right, Lower (center at x=0.8, y=0.8)
    right_lower = DetectedObject(
        label="box",
        conf=0.8,
        bbox=BoundingBox(x_min=0.75, y_min=0.75, x_max=0.85, y_max=0.85),
    )
    
    perception = PerceptionResult(
        frame_id="frame_0",
        timestamp_ms=1000,
        scene_description="Office room",
        scene_label="office",
        objects=[left_upper, center_middle, right_lower],
    )
    analysis = reasoner.analyze(perception)
    
    assert len(analysis.objects) == 3
    
    obj0 = analysis.objects[0]
    assert obj0.horizontal_zone == HorizontalZone.LEFT
    assert obj0.vertical_zone == VerticalZone.UPPER
    assert not obj0.is_central
    
    obj1 = analysis.objects[1]
    assert obj1.horizontal_zone == HorizontalZone.CENTER
    assert obj1.vertical_zone == VerticalZone.MIDDLE
    assert obj1.is_central
    
    obj2 = analysis.objects[2]
    assert obj2.horizontal_zone == HorizontalZone.RIGHT
    assert obj2.vertical_zone == VerticalZone.LOWER
    assert not obj2.is_central


def test_spatial_prominence_calculation():
    reasoner = SpatialReasoner()
    
    # Large object (area = 0.5 * 0.5 = 0.25 >= 0.12)
    large_obj = DetectedObject(
        label="table",
        conf=0.9,
        bbox=BoundingBox(x_min=0.25, y_min=0.25, x_max=0.75, y_max=0.75),
    )
    # Small object (area = 0.1 * 0.1 = 0.01 < 0.12, dim 0.1 < 0.4)
    small_obj = DetectedObject(
        label="pen",
        conf=0.8,
        bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.2),
    )
    
    perception = PerceptionResult(
        frame_id="frame_0",
        timestamp_ms=1000,
        scene_description="Desk area",
        scene_label="desk",
        objects=[large_obj, small_obj],
    )
    analysis = reasoner.analyze(perception)
    
    assert analysis.objects[0].is_prominent is True
    assert analysis.objects[1].is_prominent is False
    assert large_obj.label in [p.label for p in analysis.prominent_objects]
    assert small_obj.label not in [p.label for p in analysis.prominent_objects]


def test_spatial_bounding_box_overlap_and_relative_positions():
    reasoner = SpatialReasoner()
    
    # Overlapping objects
    obj_a = DetectedObject(
        label="person",
        conf=0.9,
        bbox=BoundingBox(x_min=0.2, y_min=0.2, x_max=0.6, y_max=0.6),
    )
    obj_b = DetectedObject(
        label="backpack",
        conf=0.85,
        bbox=BoundingBox(x_min=0.3, y_min=0.3, x_max=0.5, y_max=0.5),
    )
    # Separate object to the right
    obj_c = DetectedObject(
        label="lamp",
        conf=0.8,
        bbox=BoundingBox(x_min=0.7, y_min=0.2, x_max=0.8, y_max=0.6),
    )
    
    perception = PerceptionResult(
        frame_id="frame_0",
        timestamp_ms=1000,
        scene_description="Person with backpack",
        scene_label="hallway",
        objects=[obj_a, obj_b, obj_c],
    )
    analysis = reasoner.analyze(perception)
    
    person_info = next(o for o in analysis.objects if o.label == "person")
    backpack_info = next(o for o in analysis.objects if o.label == "backpack")
    lamp_info = next(o for o in analysis.objects if o.label == "lamp")
    
    # Overlap assertions
    assert "backpack" in person_info.overlapping_labels
    assert "person" in backpack_info.overlapping_labels
    assert "lamp" not in person_info.overlapping_labels
    
    # Relative position assertions
    assert any("left of lamp" in r for r in person_info.relative_positions)
    assert any("right of person" in r for r in lamp_info.relative_positions)


def test_spatial_empty_objects():
    reasoner = SpatialReasoner()
    perception = PerceptionResult(
        frame_id="frame_0",
        timestamp_ms=1000,
        scene_description="Empty hallway",
        scene_label="hallway",
        objects=[],
    )
    analysis = reasoner.analyze(perception)
    
    assert len(analysis.objects) == 0
    assert len(analysis.central_objects) == 0
    assert len(analysis.prominent_objects) == 0
    assert any("No objects detected" in u for u in analysis.uncertainties)


# ---------------------------------------------------------------------------
# Context Reasoning Tests
# ---------------------------------------------------------------------------

def test_context_baseline_and_persistence():
    reasoner = ContextReasoner(max_history=5)
    spatial_reasoner = SpatialReasoner()
    
    # Frame 1: person and chair
    p1 = PerceptionResult(
        frame_id="frame_1",
        timestamp_ms=1000,
        scene_description="Office room",
        scene_label="office",
        objects=[
            DetectedObject(label="person", conf=0.9, bbox=BoundingBox(x_min=0.4, y_min=0.3, x_max=0.6, y_max=0.7)),
            DetectedObject(label="chair", conf=0.85, bbox=BoundingBox(x_min=0.1, y_min=0.6, x_max=0.3, y_max=0.8)),
        ],
    )
    s1 = spatial_reasoner.analyze(p1)
    c1 = reasoner.analyze(s1, p1)
    
    # Baseline: both newly observed
    assert set(c1.new_objects) == {"person", "chair"}
    assert c1.persistent_objects == []
    assert any("Baseline observation" in ch for ch in c1.changes)
    
    # Frame 2: person remains, chair gone, table appears
    p2 = PerceptionResult(
        frame_id="frame_2",
        timestamp_ms=2000,
        scene_description="Office room",
        scene_label="office",
        objects=[
            DetectedObject(label="person", conf=0.9, bbox=BoundingBox(x_min=0.4, y_min=0.3, x_max=0.6, y_max=0.7)),
            DetectedObject(label="table", conf=0.8, bbox=BoundingBox(x_min=0.7, y_min=0.5, x_max=0.9, y_max=0.8)),
        ],
    )
    s2 = spatial_reasoner.analyze(p2)
    c2 = reasoner.analyze(s2, p2)
    
    assert c2.new_objects == ["table"]
    assert "person" in c2.persistent_objects
    assert "person" in c2.central_persistence


def test_context_scene_change_detection():
    reasoner = ContextReasoner()
    spatial_reasoner = SpatialReasoner()
    
    p1 = PerceptionResult(
        frame_id="frame_1",
        timestamp_ms=1000,
        scene_description="Corridor",
        scene_label="corridor",
        objects=[],
    )
    s1 = spatial_reasoner.analyze(p1)
    c1 = reasoner.analyze(s1, p1)
    assert not any("Scene category changed" in ch for ch in c1.changes)
    
    p2 = PerceptionResult(
        frame_id="frame_2",
        timestamp_ms=2000,
        scene_description="Courtyard",
        scene_label="courtyard",
        objects=[],
    )
    s2 = spatial_reasoner.analyze(p2)
    c2 = reasoner.analyze(s2, p2)
    assert any("Scene category changed from 'corridor' to 'courtyard'" in ch for ch in c2.changes)


# ---------------------------------------------------------------------------
# Decision Reasoning Tests (Priority & Assistance)
# ---------------------------------------------------------------------------

def test_priority_evaluation_and_assistance_categories():
    spatial_reasoner = SpatialReasoner()
    context_reasoner = ContextReasoner()
    decision_engine = AssistanceDecisionEngine()
    
    # 1. Central obstacle -> HIGH priority -> ALERT
    p_high = PerceptionResult(
        frame_id="frame_1",
        timestamp_ms=1000,
        scene_description="Hallway with obstacle",
        scene_label="hallway",
        hazards=["boulder"],
        objects=[
            DetectedObject(label="boulder", conf=0.95, bbox=BoundingBox(x_min=0.4, y_min=0.4, x_max=0.6, y_max=0.8)),
        ],
    )
    s_high = spatial_reasoner.analyze(p_high)
    c_high = context_reasoner.analyze(s_high, p_high)
    dec_high = decision_engine.decide(p_high, s_high, c_high)
    
    assert dec_high.category == AssistanceCategory.ALERT
    assert dec_high.priority == PriorityLevel.HIGH
    assert any(item.is_hazard for item in dec_high.relevant_items)
    assert "boulder" in dec_high.message
    
    # 2. Side prominent object -> MEDIUM priority -> GUIDANCE
    p_med = PerceptionResult(
        frame_id="frame_2",
        timestamp_ms=2000,
        scene_description="Room with side pillar",
        scene_label="room",
        objects=[
            # Left side, large dimension (height 0.8 >= 0.4)
            DetectedObject(label="pillar", conf=0.85, bbox=BoundingBox(x_min=0.05, y_min=0.1, x_max=0.25, y_max=0.9)),
        ],
    )
    s_med = spatial_reasoner.analyze(p_med)
    c_med = context_reasoner.analyze(s_med, p_med)
    dec_med = decision_engine.decide(p_med, s_med, c_med)
    
    assert dec_med.category == AssistanceCategory.GUIDANCE
    assert dec_med.priority == PriorityLevel.MEDIUM
    assert any(item.item == "pillar" and item.priority == PriorityLevel.MEDIUM for item in dec_med.relevant_items)
    
    # 3. Minor peripheral object -> LOW priority -> INFO
    p_low = PerceptionResult(
        frame_id="frame_3",
        timestamp_ms=3000,
        scene_description="Quiet room",
        scene_label="room",
        objects=[
            # Small corner item
            DetectedObject(label="mug", conf=0.7, bbox=BoundingBox(x_min=0.8, y_min=0.8, x_max=0.85, y_max=0.85)),
        ],
    )
    s_low = spatial_reasoner.analyze(p_low)
    c_low = context_reasoner.analyze(s_low, p_low)
    dec_low = decision_engine.decide(p_low, s_low, c_low)
    
    assert dec_low.category == AssistanceCategory.INFO
    assert dec_low.priority == PriorityLevel.LOW
    
    # 4. Completely empty perception -> NONE
    p_none = PerceptionResult(frame_id="frame_4", timestamp_ms=4000, scene_description="", scene_label="", objects=[])
    s_none = spatial_reasoner.analyze(p_none)
    c_none = context_reasoner.analyze(s_none, p_none)
    dec_none = decision_engine.decide(p_none, s_none, c_none)
    assert dec_none.category == AssistanceCategory.NONE
