"""
Interface contract for A-Eye Track 1 Perception Subsystem.

Defines PerceptionResult and nested models for inter-track communication
between Track 1 (Perception), Track 2 (Reasoning), and Track 3 (App/UI).

CONTRACT_VERSION = "0.1-draft"
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

CONTRACT_VERSION = "0.1-draft"


class MotionVector(BaseModel):
    """
    Apparent image motion of a tracked object bounding box.

    Units:
    - dx: change in normalized box center X per second (positive = rightward in image)
    - dy: change in normalized box center Y per second (positive = downward in image)
    - growth: change in normalized box area (w * h) per second (positive = expanding in image)

    NOTE: This represents APPARENT 2D IMAGE MOTION ONLY, not 3D physical velocity
    or collision risk.
    """
    dx: float = Field(..., description="Normalized X-center velocity per second")
    dy: float = Field(..., description="Normalized Y-center velocity per second")
    growth: float = Field(..., description="Normalized box area growth rate per second")


class DetectedObject(BaseModel):
    """
    An obstacle or object detection in a single frame.

    Bounding Box: [x1, y1, x2, y2], normalized in range [0.0, 1.0].
    Origin is top-left corner, x pointing right, y pointing downward.
    """
    label: str = Field(..., description="Class name of the detected object")
    conf: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    bbox: List[float] = Field(..., description="Normalized bounding box [x1, y1, x2, y2]")
    track_id: Optional[int] = Field(None, description="Persistent track ID assigned by tracker")
    motion: Optional[MotionVector] = Field(None, description="Apparent 2D image motion vector")

    @field_validator("bbox")
    @classmethod
    def validate_and_clamp_bbox(cls, v: List[float]) -> List[float]:
        if len(v) != 4:
            raise ValueError(f"Bounding box must contain exactly 4 elements [x1, y1, x2, y2], got {len(v)}")
        # Clamp values to [0.0, 1.0] range
        x1, y1, x2, y2 = [max(0.0, min(1.0, float(x))) for x in v]
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        return [round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)]


class TextBlock(BaseModel):
    """
    Extracted text block region from OCR.
    """
    text: str = Field(..., description="Recognized text string")
    conf: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score [0.0, 1.0]")
    bbox: List[float] = Field(..., description="Normalized bounding box [x1, y1, x2, y2]")

    @field_validator("bbox")
    @classmethod
    def validate_and_clamp_bbox(cls, v: List[float]) -> List[float]:
        if len(v) != 4:
            raise ValueError(f"Bounding box must contain exactly 4 elements [x1, y1, x2, y2], got {len(v)}")
        x1, y1, x2, y2 = [max(0.0, min(1.0, float(x))) for x in v]
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        return [round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)]


class PerceptionResult(BaseModel):
    """
    Unified perception frame output produced by Track 1.
    """
    frame_id: int = Field(..., ge=0, description="Monotonically increasing frame index")
    timestamp_ms: int = Field(..., ge=0, description="Epoch timestamp in milliseconds")
    source: Literal["offline", "online"] = Field(..., description="Pipeline path producing detection")
    objects: List[DetectedObject] = Field(default_factory=list, description="List of detected objects")
    text_blocks: List[TextBlock] = Field(default_factory=list, description="List of OCR text blocks")
    scene_label: Optional[str] = Field(None, description="Macro scene classification label")
    scene_description: Optional[str] = Field(
        None, description="Natural language scene description (populated ONLY on online path)"
    )
    contract_version: str = Field(default=CONTRACT_VERSION, description="Contract version")

    @model_validator(mode="after")
    def validate_scene_description_for_source(self) -> "PerceptionResult":
        if self.source == "offline" and self.scene_description is not None:
            raise ValueError("scene_description must be None when source is 'offline'")
        return self

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "PerceptionResult":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)
