
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
