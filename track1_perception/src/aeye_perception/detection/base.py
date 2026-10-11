"""
Abstract base class and mock implementation for object detectors.

Defines the unified interface for converting raw image numpy frames into
contract-compliant List[DetectedObject] instances.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from aeye_perception.contract import DetectedObject


class AbstractDetector(ABC):
    """
    Abstract Base Class for all Track 1 obstacle detectors.
    """

    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[DetectedObject]:
        """
        Detect objects in an input BGR numpy image frame.

        Parameters:
        - image: BGR image as uint8 numpy array [H, W, 3]
        - conf_threshold: Optional confidence override score [0.0, 1.0]
        - iou_threshold: Optional NMS IoU threshold override [0.0, 1.0]

        Returns:
        - List of contract-compliant DetectedObject instances with normalized bboxes.
        """
        pass


class MockDetector(AbstractDetector):
    """
    Deterministic mock detector for offline testing and fast stream simulation.
    Does not require PyTorch or downloaded model weights.
    """

    def __init__(
        self,
        preset_objects: Optional[List[DetectedObject]] = None,
        default_conf: float = 0.85,
    ):
        self.preset_objects = preset_objects
        self.default_conf = default_conf

    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[DetectedObject]:
        effective_conf = conf_threshold if conf_threshold is not None else self.default_conf

        if self.preset_objects is not None:
            return [
                obj for obj in self.preset_objects
                if obj.conf >= effective_conf
            ]

        # Default synthetic detections
        default_dets = [
            DetectedObject(
                label="chair",
                conf=0.88,
                bbox=[0.35, 0.45, 0.55, 0.85],
                track_id=None,
                motion=None,
            ),
            DetectedObject(
                label="door",
                conf=0.92,
                bbox=[0.05, 0.10, 0.30, 0.90],
                track_id=None,
                motion=None,
            ),
        ]

        return [d for d in default_dets if d.conf >= effective_conf]
