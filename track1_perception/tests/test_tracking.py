
import pytest

from aeye_perception.contract import DetectedObject
from aeye_perception.tracking import IoUTracker


def detection(label="chair", bbox=None, conf=0.9):
    return DetectedObject(
        label=label,
        conf=conf,
        bbox=bbox or [0.1, 0.1, 0.3, 0.3],
    )


def test_assigns_id_to_new_detection():
    tracker = IoUTracker()
    result = tracker.update([detection()], timestamp_ms=1000)

    assert len(result) == 1
    assert result[0].track_id == 1
    assert result[0].motion is None


def test_preserves_id_when_object_moves_slightly():
    tracker = IoUTracker()
    first = tracker.update(
        [detection(bbox=[0.1, 0.1, 0.3, 0.3])],
        timestamp_ms=1000,
    )
    second = tracker.update(
        [detection(bbox=[0.11, 0.1, 0.31, 0.3])],
        timestamp_ms=2000,
    )

    assert second[0].track_id == first[0].track_id
    assert second[0].motion is not None
    assert second[0].motion.dx == pytest.approx(0.01)
    assert second[0].motion.dy == pytest.approx(0.0)


def test_different_labels_do_not_share_track():
    tracker = IoUTracker()
    tracker.update([detection("chair")], timestamp_ms=1000)

    result = tracker.update(
        [detection("bottle")],
        timestamp_ms=2000,
    )

    assert result[0].track_id == 2
    assert result[0].motion is None


def test_temporarily_missing_detection_can_reuse_track():
    tracker = IoUTracker(max_missed_frames=2)
    first = tracker.update([detection()], timestamp_ms=1000)

    tracker.update([], timestamp_ms=2000)
    result = tracker.update(
        [detection(bbox=[0.11, 0.1, 0.31, 0.3])],
        timestamp_ms=3000,
    )

    assert result[0].track_id == first[0].track_id
    assert result[0].motion is None


def test_track_expires_after_missed_frame_limit():
    tracker = IoUTracker(max_missed_frames=1)
    tracker.update([detection()], timestamp_ms=1000)

    tracker.update([], timestamp_ms=2000)
    tracker.update([], timestamp_ms=3000)
    result = tracker.update([detection()], timestamp_ms=4000)

    assert result[0].track_id == 2


def test_rejects_non_increasing_timestamps():
    tracker = IoUTracker()
    tracker.update([detection()], timestamp_ms=1000)

    with pytest.raises(ValueError, match="timestamps must increase"):
        tracker.update([detection()], timestamp_ms=1000)


def test_reset_clears_tracks_and_restarts_ids():
    tracker = IoUTracker()
    tracker.update([detection()], timestamp_ms=1000)

    tracker.reset()
    result = tracker.update([detection()], timestamp_ms=1000)

    assert result[0].track_id == 1
    assert result[0].motion is None


def test_does_not_mutate_input_detection():
    tracker = IoUTracker()
    original = detection()

    tracker.update([original], timestamp_ms=1000)

    assert original.track_id is None
    assert original.motion is None


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        IoUTracker(iou_threshold=1.5)

    with pytest.raises(ValueError):
        IoUTracker(max_missed_frames=-1)


def test_tracks_two_same_class_objects_independently():
    tracker = IoUTracker()

    first_frame = tracker.update(
        [
            detection("chair", [0.05, 0.1, 0.25, 0.4]),
            detection("chair", [0.65, 0.1, 0.85, 0.4]),
        ],
        timestamp_ms=1000,
    )

    second_frame = tracker.update(
        [
            detection("chair", [0.08, 0.1, 0.28, 0.4]),
            detection("chair", [0.62, 0.1, 0.82, 0.4]),
        ],
        timestamp_ms=2000,
    )

    assert first_frame[0].track_id != first_frame[1].track_id
    assert second_frame[0].track_id == first_frame[0].track_id
    assert second_frame[1].track_id == first_frame[1].track_id


def test_crossing_objects_keep_ids_when_iou_matching_is_unambiguous():
    tracker = IoUTracker(iou_threshold=0.1)

    first_frame = tracker.update(
        [
            detection("chair", [0.10, 0.1, 0.30, 0.4]),
            detection("chair", [0.60, 0.1, 0.80, 0.4]),
        ],
        timestamp_ms=1000,
    )

    # The chairs move toward each other but remain spatially distinguishable.
    second_frame = tracker.update(
        [
            detection("chair", [0.25, 0.1, 0.45, 0.4]),
            detection("chair", [0.45, 0.1, 0.65, 0.4]),
        ],
        timestamp_ms=2000,
    )

    assert second_frame[0].track_id == first_frame[0].track_id
    assert second_frame[1].track_id == first_frame[1].track_id


def test_identical_detection_boxes_document_tiebreaking_not_physical_identity():
    """Identical bounding boxes cannot reveal true physical object identity.

    When multiple detections have identical boxes and equal IoU with existing tracks,
    the tracker cannot resolve physical identities. This test verifies that the tracker
    behaves deterministically: both tracks are preserved without duplicate ID assignment,
    resolved via deterministic greedy tie-breaking rather than physical identity recovery.
    """
    tracker = IoUTracker(iou_threshold=0.1)

    first_frame = tracker.update(
        [
            detection("chair", [0.10, 0.1, 0.50, 0.5]),
            detection("chair", [0.50, 0.1, 0.90, 0.5]),
        ],
        timestamp_ms=1000,
    )

    # Both detections now have identical boxes and equal IoU with both tracks.
    # Image geometry alone cannot distinguish which detection corresponds to which physical object.
    ambiguous_frame = tracker.update(
        [
            detection("chair", [0.30, 0.1, 0.70, 0.5]),
            detection("chair", [0.30, 0.1, 0.70, 0.5]),
        ],
        timestamp_ms=2000,
    )

    # Both original track IDs are preserved without duplicate assignment.
    assigned_ids = {ambiguous_frame[0].track_id, ambiguous_frame[1].track_id}
    expected_ids = {first_frame[0].track_id, first_frame[1].track_id}
    assert assigned_ids == expected_ids
    assert ambiguous_frame[0].track_id != ambiguous_frame[1].track_id


def test_crossing_objects_maintain_identity():
    """Regression test: two crossing objects with consistent velocity should maintain their IDs.

    Under naive IoU-only matching, after passing each other, the left-moving object overlaps more
    with the previous position of the right-moving object, causing an ID swap.
    """
    tracker = IoUTracker(iou_threshold=0.2)

    # Frame 1: Obj 1 moving right (starts at 0.20), Obj 2 moving left (starts at 0.50)
    f1 = tracker.update(
        [
            detection("chair", [0.20, 0.20, 0.40, 0.40]),
            detection("chair", [0.50, 0.20, 0.70, 0.40]),
        ],
        timestamp_ms=1000,
    )
    id1 = f1[0].track_id
    id2 = f1[1].track_id

    # Frame 2: They approach each other (Obj 1 moves right +0.12, Obj 2 moves left -0.12)
    f2 = tracker.update(
        [
            detection("chair", [0.32, 0.20, 0.52, 0.40]),
            detection("chair", [0.38, 0.20, 0.58, 0.40]),
        ],
        timestamp_ms=2000,
    )
    assert f2[0].track_id == id1
    assert f2[1].track_id == id2

    # Frame 3: They cross each other and continue along their trajectories
    # Obj 2 is now on the left (0.26), Obj 1 is on the right (0.44)
    f3 = tracker.update(
        [
            detection("chair", [0.26, 0.20, 0.46, 0.40]),  # Obj 2 (moving left)
            detection("chair", [0.44, 0.20, 0.64, 0.40]),  # Obj 1 (moving right)
        ],
        timestamp_ms=3000,
    )
    # Ground truth: detection 0 (at 0.26) is Obj 2 (id2), detection 1 (at 0.44) is Obj 1 (id1)
    assert f3[0].track_id == id2
    assert f3[1].track_id == id1


def test_motion_prediction_disabled_reproduces_id_swap():
    """Verify that disabling motion prediction falls back to naive greedy IoU behavior."""
    tracker = IoUTracker(iou_threshold=0.2, use_motion_prediction=False)

    f1 = tracker.update(
        [
            detection("chair", [0.20, 0.20, 0.40, 0.40]),
            detection("chair", [0.50, 0.20, 0.70, 0.40]),
        ],
        timestamp_ms=1000,
    )
    id1 = f1[0].track_id
    id2 = f1[1].track_id

    tracker.update(
        [
            detection("chair", [0.32, 0.20, 0.52, 0.40]),
            detection("chair", [0.38, 0.20, 0.58, 0.40]),
        ],
        timestamp_ms=2000,
    )

    # Frame 3: Without motion prediction, greedy IoU associates det 0 (at 0.26)
    # with track 1's previous position (0.32) because overlap 0.54 > 0.25.
    f3 = tracker.update(
        [
            detection("chair", [0.26, 0.20, 0.46, 0.40]),
            detection("chair", [0.44, 0.20, 0.64, 0.40]),
        ],
        timestamp_ms=3000,
    )
    assert f3[0].track_id == id1  # ID swap occurs
    assert f3[1].track_id == id2


def test_fast_moving_object_retained_by_motion_prediction():
    """Fast object whose static IoU drops below threshold is preserved by motion prediction."""
    tracker_smooth = IoUTracker(iou_threshold=0.30, use_motion_prediction=True)
    t1 = tracker_smooth.update(
        [detection("chair", [0.10, 0.20, 0.25, 0.35])],
        timestamp_ms=1000,
    )
    # Step 1: displacement 0.05, static IoU is 0.10 / 0.20 = 0.50 >= 0.30
    t2 = tracker_smooth.update(
        [detection("chair", [0.15, 0.20, 0.30, 0.35])],
        timestamp_ms=2000,
    )
    assert t2[0].track_id == t1[0].track_id
    assert t2[0].motion.dx == pytest.approx(0.05)

    # Step 2: continues at same speed (displacement 0.05) -> [0.20, 0.20, 0.35, 0.35]
    # Predicted box is [0.20, 0.20, 0.35, 0.35], IoU = 1.0!
    t3 = tracker_smooth.update(
        [detection("chair", [0.20, 0.20, 0.35, 0.35])],
        timestamp_ms=3000,
    )
    assert t3[0].track_id == t1[0].track_id
    assert t3[0].motion.dx == pytest.approx(0.05)


def test_abrupt_stop_preserves_track_identity():
    """An object moving at constant speed that abruptly stops retains its track identity."""
    tracker = IoUTracker(iou_threshold=0.30, use_motion_prediction=True)

    t1 = tracker.update(
        [detection("chair", [0.10, 0.20, 0.30, 0.40])],
        timestamp_ms=1000,
    )
    t2 = tracker.update(
        [detection("chair", [0.18, 0.20, 0.38, 0.40])],
        timestamp_ms=2000,
    )
    assert t2[0].track_id == t1[0].track_id
    assert t2[0].motion.dx == pytest.approx(0.08)

    # In frame 3, the object stops completely and stays at [0.18, 0.20, 0.38, 0.40]
    # Static IoU is 1.0, so the track is maintained despite the nonzero prior velocity
    t3 = tracker.update(
        [detection("chair", [0.18, 0.20, 0.38, 0.40])],
        timestamp_ms=3000,
    )
    assert t3[0].track_id == t1[0].track_id
    assert t3[0].motion.dx == pytest.approx(0.0)


def test_missed_frame_resets_velocity_to_prevent_drift():
    """A track that misses a frame does not extrapolate its old velocity across gaps."""
    tracker = IoUTracker(iou_threshold=0.30, max_missed_frames=2, use_motion_prediction=True)

    t1 = tracker.update(
        [detection("chair", [0.10, 0.20, 0.30, 0.40])],
        timestamp_ms=1000,
    )
    t2 = tracker.update(
        [detection("chair", [0.15, 0.20, 0.35, 0.40])],
        timestamp_ms=2000,
    )
    assert t2[0].track_id == t1[0].track_id

    # Frame 3: missed detection
    tracker.update([], timestamp_ms=3000)

    # Frame 4: object reappears at static location [0.15, 0.20, 0.35, 0.40]
    t4 = tracker.update(
        [detection("chair", [0.15, 0.20, 0.35, 0.40])],
        timestamp_ms=4000,
    )
    assert t4[0].track_id == t1[0].track_id
    assert t4[0].motion is None  # Motion is not computed across missed gap
