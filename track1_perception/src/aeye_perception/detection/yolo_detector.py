"""
Ultralytics YOLO obstacle detector wrapper.

Converts raw PyTorch / Ultralytics bounding box predictions into normalized
contract-compliant List[DetectedObject] objects.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import yaml

from aeye_perception.contract import DetectedObject
from aeye_perception.detection.base import AbstractDetector
from aeye_perception.geometry import normalize_bbox

logger = logging.getLogger(__name__)


# Narrowly scoped set of recognized Ultralytics pretrained detection weights
SUPPORTED_PRETRAINED_MODELS = {
    # YOLOv8 detection
    "yolov8n.pt",
    "yolov8s.pt",
    "yolov8m.pt",
    "yolov8l.pt",
    "yolov8x.pt",
    # YOLO11 detection
    "yolo11n.pt",
    "yolo11s.pt",
    "yolo11m.pt",
    "yolo11l.pt",
    "yolo11x.pt",
    # YOLOv5u detection
    "yolov5nu.pt",
    "yolov5su.pt",
    "yolov5mu.pt",
}


class YOLOObstacleDetector(AbstractDetector):
    """
    Ultralytics YOLO detection wrapper for obstacle recognition.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        config_path: Optional[Union[str, Path]] = "configs/default.yaml",
        labels_path: Optional[Union[str, Path]] = "configs/detector_labels.yaml",
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        device: str = "auto",
        use_custom_labels: bool = False,
    ):
        self.model_path = model_path
        self.config_path = Path(config_path) if config_path else None
        self.labels_path = Path(labels_path) if labels_path else None
        self.device = device
        self.use_custom_labels = use_custom_labels
        self._model = None

        # Load default settings from config file if available
        self.conf_threshold = conf_threshold if conf_threshold is not None else 0.35
        self.iou_threshold = iou_threshold if iou_threshold is not None else 0.45

        if self.config_path and self.config_path.exists():
            with open(self.config_path, "r") as f:
                cfg = yaml.safe_load(f)
                if conf_threshold is None:
                    self.conf_threshold = cfg.get("thresholds", {}).get("detection_conf", 0.35)
                if iou_threshold is None:
                    self.iou_threshold = cfg.get("nms", {}).get("iou_threshold", 0.45)
                if device == "auto":
                    self.device = cfg.get("device", "auto")

        # Load target class labels from labels config
        self.target_labels: Dict[int, str] = {}
        if self.labels_path and self.labels_path.exists():
            with open(self.labels_path, "r") as f:
                lbl_cfg = yaml.safe_load(f)
                self.target_labels = {int(k): str(v) for k, v in lbl_cfg.get("classes", {}).items()}

    def _load_model(self):
        """Lazy load Ultralytics YOLO model."""
        if self._model is not None:
            return self._model

        # Verify local weights exist, allowing download only for recognized pretrained model names
        model_path_obj = Path(self.model_path)
        is_supported_downloadable = (
            len(model_path_obj.parts) == 1
            and model_path_obj.name.lower() in SUPPORTED_PRETRAINED_MODELS
        )
        if not model_path_obj.exists() and not is_supported_downloadable:
            raise FileNotFoundError(f"Model weights file not found at '{self.model_path}'")

        try:
            from ultralytics import YOLO
            import torch
        except ImportError as e:
            raise ImportError(
                "Ultralytics YOLO or PyTorch is not installed. "
                "Please install the detection extras using: pip install -e \".[detection]\""
            ) from e

        # Resolve device
        resolved_device = "cpu"
        if self.device == "cuda" or (self.device == "auto" and torch.cuda.is_available()):
            resolved_device = "cuda"

        logger.info(f"Loading YOLO model from '{self.model_path}' on device '{resolved_device}'")
        try:
            self._model = YOLO(self.model_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Model weights file not found at '{self.model_path}'") from e

        self.resolved_device = resolved_device
        return self._model

    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[DetectedObject]:
        """
        Run obstacle detection on a BGR numpy image frame [H, W, 3].
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Input image must be a non-empty BGR uint8 numpy array.")

        img_h, img_w = image.shape[:2]
        effective_conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        effective_iou = iou_threshold if iou_threshold is not None else self.iou_threshold

        model = self._load_model()

        # Run inference
        results = model.predict(
            source=image,
            conf=effective_conf,
            iou=effective_iou,
            device=self.resolved_device,
            verbose=False,
        )

        detected_objects: List[DetectedObject] = []
        if not results:
            return detected_objects

        result = results[0]
        if not hasattr(result, "boxes") or result.boxes is None:
            return detected_objects

        boxes = result.boxes
        names = getattr(result, "names", {})

        for box in boxes:
            # Extract box coordinates xyxy in pixels
            xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy[0], "tolist") else list(box.xyxy[0])
            conf_val = float(box.conf[0]) if hasattr(box.conf[0], "item") else float(box.conf[0])
            cls_id = int(box.cls[0]) if hasattr(box.cls[0], "item") else int(box.cls[0])

            # Class label lookup: preserve model's native class name unless use_custom_labels=True
            raw_label = names.get(cls_id, str(cls_id))
            if self.use_custom_labels and cls_id in self.target_labels:
                label_str = self.target_labels[cls_id]
            else:
                label_str = raw_label

            # Convert pixel coordinates to normalized [x1, y1, x2, y2]
            norm_bbox = normalize_bbox(xyxy, img_w, img_h)

            detected_objects.append(
                DetectedObject(
                    label=label_str,
                    conf=round(conf_val, 4),
                    bbox=norm_bbox,
                    track_id=None,
                    motion=None,
                )
            )

        return detected_objects
