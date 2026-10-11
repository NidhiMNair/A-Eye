"""
Detection module for A-Eye Track 1 Perception.

Provides AbstractDetector base class, MockDetector, and YOLOObstacleDetector.
"""

from aeye_perception.detection.base import AbstractDetector, MockDetector
from aeye_perception.detection.yolo_detector import YOLOObstacleDetector

__all__ = [
    "AbstractDetector",
    "MockDetector",
    "YOLOObstacleDetector",
]
