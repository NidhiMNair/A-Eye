"""
Offline unit tests for WP1.1 Object Detector module.

Tests AbstractDetector, MockDetector, and YOLOObstacleDetector without downloading
model weights or requiring PyTorch/ultralytics during standard pytest runs.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from aeye_perception.contract import DetectedObject
from aeye_perception.detection.base import AbstractDetector, MockDetector
from aeye_perception.detection.yolo_detector import YOLOObstacleDetector


def test_mock_detector_default_detections():
    """Verify MockDetector produces valid normalized DetectedObject instances."""
    detector = MockDetector()
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    dets = detector.detect(img)
    assert len(dets) == 2
    assert isinstance(dets[0], DetectedObject)
    assert dets[0].label == "chair"
    assert dets[0].track_id is None
    assert dets[0].motion is None
    assert dets[0].bbox == [0.35, 0.45, 0.55, 0.85]


def test_mock_detector_conf_filtering():
    """Verify threshold filtering in MockDetector."""
    detector = MockDetector()
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Threshold 0.90 filters out chair (0.88) and keeps door (0.92)
    dets = detector.detect(img, conf_threshold=0.90)
    assert len(dets) == 1
    assert dets[0].label == "door"

    # High threshold 0.99 returns empty list
    dets_empty = detector.detect(img, conf_threshold=0.99)
    assert len(dets_empty) == 0


def test_mock_detector_custom_preset():
    """Verify MockDetector with custom preset objects."""
    custom_obj = DetectedObject(
        label="staircase_step",
        conf=0.95,
        bbox=[0.1, 0.2, 0.8, 0.9],
    )
    detector = MockDetector(preset_objects=[custom_obj])
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    dets = detector.detect(img)
    assert len(dets) == 1
    assert dets[0].label == "staircase_step"


def test_yolo_detector_normalization_mocked():
    """Verify YOLOObstacleDetector box normalization with mocked YOLO model."""
    img_w, img_h = 640, 480
    fake_img = np.zeros((img_h, img_w, 3), dtype=np.uint8)

    # Create mock prediction result
    mock_box = MagicMock()
    mock_box.xyxy = [np.array([64.0, 48.0, 320.0, 240.0])]  # [x1, y1, x2, y2] in pixels
    mock_box.conf = [np.array(0.85)]
    mock_box.cls = [np.array(0)]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person"}

    mock_yolo_instance = MagicMock()
    mock_yolo_instance.predict.return_value = [mock_result]

    detector = YOLOObstacleDetector(config_path=None, labels_path=None)
    detector._model = mock_yolo_instance
    detector.resolved_device = "cpu"

    dets = detector.detect(fake_img, conf_threshold=0.5)

    assert len(dets) == 1
    det = dets[0]
    assert det.label == "person"
    assert det.conf == 0.85
    # Pixel [64, 48, 320, 240] on 640x480 -> normalized [0.1, 0.1, 0.5, 0.5]
    assert det.bbox == [0.1, 0.1, 0.5, 0.5]
    assert det.track_id is None
    assert det.motion is None


def test_yolo_detector_missing_dependency_error():
    """Verify clean ImportError when ultralytics or torch is not installed."""
    detector = YOLOObstacleDetector(config_path=None, labels_path=None)
    detector._model = None  # Force load attempt

    with patch.dict("sys.modules", {"ultralytics": None}):
        with pytest.raises(ImportError) as excinfo:
            detector._load_model()
        assert "pip install -e \".[detection]\"" in str(excinfo.value)


def test_yolo_detector_class_label_preservation():
    """Verify that pretrained models preserve native names and only custom mode remaps."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Mock detection with class ID 1 (which is 'bicycle' in COCO, but 'chair' in detector_labels.yaml)
    mock_box = MagicMock()
    mock_box.xyxy = [np.array([10.0, 10.0, 100.0, 100.0])]
    mock_box.conf = [np.array(0.90)]
    mock_box.cls = [np.array(1)]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_result.names = {1: "bicycle"}

    mock_yolo = MagicMock()
    mock_yolo.predict.return_value = [mock_result]

    # 1. Standard mode (use_custom_labels=False, default): MUST preserve 'bicycle'
    detector_standard = YOLOObstacleDetector(config_path=None, labels_path="configs/detector_labels.yaml", use_custom_labels=False)
    detector_standard._model = mock_yolo
    detector_standard.resolved_device = "cpu"
    dets_standard = detector_standard.detect(img)
    assert dets_standard[0].label == "bicycle"

    # 2. Custom mode (use_custom_labels=True): remaps class 1 to 'chair' from detector_labels.yaml
    detector_custom = YOLOObstacleDetector(config_path=None, labels_path="configs/detector_labels.yaml", use_custom_labels=True)
    detector_custom._model = mock_yolo
    detector_custom.resolved_device = "cpu"
    dets_custom = detector_custom.detect(img)
    assert dets_custom[0].label == "chair"


def test_yolo_detector_missing_weight_file_error():
    """Verify that nonexistent local weight paths with directories raise a clean FileNotFoundError."""
    detector = YOLOObstacleDetector(model_path="models/non_existent_weights.pt")
    with pytest.raises(FileNotFoundError) as excinfo:
        detector._load_model()
    assert "Model weights file not found" in str(excinfo.value)
    assert "models/non_existent_weights.pt" in str(excinfo.value)


def test_yolo_detector_missing_single_filename_error():
    """Verify that nonexistent single-filename local paths raise a clean FileNotFoundError."""
    detector = YOLOObstacleDetector(model_path="non_existent.pt")
    with pytest.raises(FileNotFoundError) as excinfo:
        detector._load_model()
    assert "Model weights file not found" in str(excinfo.value)
    assert "non_existent.pt" in str(excinfo.value)


def test_yolo_detector_recognized_pretrained_allows_download():
    """Verify that recognized pretrained models (like yolov8n.pt) pass whitelist and invoke YOLO."""
    detector = YOLOObstacleDetector(model_path="yolov8n.pt")

    mock_ultralytics = MagicMock()
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_yolo_cls = MagicMock()
    mock_model_instance = MagicMock()
    mock_yolo_cls.return_value = mock_model_instance
    mock_ultralytics.YOLO = mock_yolo_cls

    with patch.dict("sys.modules", {"ultralytics": mock_ultralytics, "torch": mock_torch}):
        model = detector._load_model()
        mock_yolo_cls.assert_called_once_with("yolov8n.pt")
        assert model is mock_model_instance


