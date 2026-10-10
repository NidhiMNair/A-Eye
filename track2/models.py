"""
track2/models.py
==================
Core data structures and contracts for Track 2.

All Track 2 models are defined here:
  - Input: Frame, FrameBatch
  - Perception: BoundingBox, DetectedObject, PerceptionResult
  - Spatial: HorizontalZone, VerticalZone, SpatialObjectInfo, SpatialAnalysis
  - Context: ContextAnalysis
  - Priority & Assistance: PriorityLevel, PrioritizedItem, AssistanceCategory, AssistanceDecision
  - Pipeline Output: Track2Result
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterator, Optional, Sequence, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Frame & FrameBatch ────────────────────────────────────────────────────────

class Frame(BaseModel):
    """
    Represents a single camera frame entering Track 2.

    Attributes:
      - frame_id: Unique string identifying the frame.
      - timestamp: Non-negative capture timestamp (seconds or milliseconds).
      - data: Raw image data buffer (bytes, bytearray, or file path).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    frame_id: str = Field(..., description="Unique frame identifier")
    timestamp: Union[int, float] = Field(..., description="Timestamp of frame capture")
    data: Any = Field(..., description="Image or frame buffer data")

    def __init__(
        self,
        frame_id: Optional[str] = None,
        timestamp: Optional[Union[int, float]] = None,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        if data is None:
            data = kwargs.pop("image", kwargs.pop("image_data", kwargs.pop("frame_data", None)))
        if timestamp is None:
            timestamp = kwargs.pop("timestamp_ms", None)

        init_kwargs: dict[str, Any] = {}
        if frame_id is not None:
            init_kwargs["frame_id"] = frame_id
        if timestamp is not None:
            init_kwargs["timestamp"] = timestamp
        if data is not None:
            init_kwargs["data"] = data
        init_kwargs.update(kwargs)

        super().__init__(**init_kwargs)

    @field_validator("frame_id", mode="before")
    @classmethod
    def _validate_frame_id(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("frame_id must be a non-empty string")
        return v.strip()

    @field_validator("timestamp", mode="before")
    @classmethod
    def _validate_timestamp(cls, v: Any) -> Union[int, float]:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError("timestamp must be an int or float")
        if v < 0:
            raise ValueError(f"timestamp must be non-negative, got {v}")
        return v

    @field_validator("data", mode="before")
    @classmethod
    def _validate_data(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("data cannot be None")
        if hasattr(v, "__len__") and len(v) == 0:
            raise ValueError("data cannot be empty")
        return v

    @property
    def image(self) -> Any:
        return self.data

    @property
    def image_data(self) -> Any:
        return self.data

    @property
    def frame_data(self) -> Any:
        return self.data

    @property
    def timestamp_ms(self) -> int:
        if self.timestamp >= 1000:
            return int(self.timestamp)
        return int(self.timestamp * 1000)


class FrameBatch:
    """
    Represents an ordered collection of one or more Frame objects.
    Does not enforce a fixed batch size.
    """

    def __init__(
        self,
        frames: Optional[Union[Sequence[Frame], Frame]] = None,
        *var_frames: Frame,
    ) -> None:
        resolved: list[Frame] = []
        if frames is not None:
            if isinstance(frames, (list, tuple)):
                resolved = list(frames)
            elif isinstance(frames, Frame):
                resolved = [frames]
            elif hasattr(frames, "__iter__"):
                resolved = list(frames)
            else:
                raise TypeError(f"Expected a sequence of Frame objects, got {type(frames).__name__}")

        if var_frames:
            resolved.extend(var_frames)

        if not resolved:
            raise ValueError("FrameBatch must contain at least one Frame")

        for idx, item in enumerate(resolved):
            if not isinstance(item, Frame):
                raise TypeError(
                    f"FrameBatch element at index {idx} must be a Frame instance, got {type(item).__name__}"
                )

        self._frames: list[Frame] = resolved

    @property
    def frames(self) -> list[Frame]:
        return list(self._frames)

    @property
    def first_frame(self) -> Frame:
        return self._frames[0]

    @property
    def latest_frame(self) -> Frame:
        return self._frames[-1]

    @property
    def frame_ids(self) -> list[str]:
        return [f.frame_id for f in self._frames]

    def __len__(self) -> int:
        return len(self._frames)

    def __iter__(self) -> Iterator[Frame]:
        return iter(self._frames)

    def __getitem__(self, index: Union[int, slice]) -> Union[Frame, list[Frame]]:
        if isinstance(index, slice):
            return self._frames[index]
        return self._frames[index]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FrameBatch):
            return False
        return self._frames == other._frames

    def __repr__(self) -> str:
        return f"FrameBatch(frames={self._frames!r})"


# ── Perception Models ─────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """
    Normalized 2D bounding box in image coordinates [0.0, 1.0].
    Enforces x_min < x_max and y_min < y_max.
    """

    x_min: float = Field(..., ge=0.0, le=1.0, description="Normalized left edge [0, 1]")
    y_min: float = Field(..., ge=0.0, le=1.0, description="Normalized top edge [0, 1]")
    x_max: float = Field(..., ge=0.0, le=1.0, description="Normalized right edge [0, 1]")
    y_max: float = Field(..., ge=0.0, le=1.0, description="Normalized bottom edge [0, 1]")

    @model_validator(mode="after")
    def _check_bounds(self) -> "BoundingBox":
        if self.x_min >= self.x_max:
            raise ValueError(f"x_min ({self.x_min}) must be strictly less than x_max ({self.x_max})")
        if self.y_min >= self.y_max:
            raise ValueError(f"y_min ({self.y_min}) must be strictly less than y_max ({self.y_max})")
        return self

    @property
    def width(self) -> float:
        return round(self.x_max - self.x_min, 4)

    @property
    def height(self) -> float:
        return round(self.y_max - self.y_min, 4)

    @property
    def area(self) -> float:
        return round(self.width * self.height, 4)

    @property
    def center_x(self) -> float:
        return round((self.x_min + self.x_max) / 2.0, 4)

    @property
    def center_y(self) -> float:
        return round((self.y_min + self.y_max) / 2.0, 4)

    def overlaps(self, other: "BoundingBox") -> bool:
        """Returns True if this bounding box overlaps with another bounding box."""
        if self.x_max <= other.x_min or other.x_max <= self.x_min:
            return False
        if self.y_max <= other.y_min or other.y_max <= self.y_min:
            return False
        return True


class DetectedObject(BaseModel):
    """A detected object in image coordinates."""

    label: str = Field(..., min_length=1, description="Object category label")
    conf: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")
    bbox: BoundingBox = Field(..., description="Normalized bounding box")
    track_id: Optional[int] = Field(None, description="Optional tracker identifier")

    @property
    def confidence(self) -> float:
        return self.conf

    @property
    def bounding_box(self) -> BoundingBox:
        return self.bbox


class PerceptionResult(BaseModel):
    """
    Structured perception result produced by the VLM.
    Conforms to the Track 2 perception schema.
    """

    frame_id: str = Field(..., description="Associated frame identifier")
    timestamp_ms: int = Field(..., ge=0, description="Timestamp in milliseconds")
    source: str = Field(default="online", description="Perception source ('online' or 'offline')")
    objects: list[DetectedObject] = Field(default_factory=list, description="Detected objects")
    scene_label: str = Field(default="general", description="Coarse category for the scene")
    scene_description: Optional[str] = Field(None, description="Concise visible scene description")
    spatial_relationships: list[str] = Field(default_factory=list, description="Spatial relationships")
    hazards: list[str] = Field(default_factory=list, description="Supported obstacles / hazards")
    uncertainties: list[str] = Field(default_factory=list, description="Known uncertainties")

    model_config = ConfigDict(extra="ignore")


# ── Spatial Reasoning Models ──────────────────────────────────────────────────

class HorizontalZone(str, Enum):
    """Image-space horizontal zone."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalZone(str, Enum):
    """Image-space vertical zone."""
    UPPER = "upper"
    MIDDLE = "middle"
    LOWER = "lower"


class SpatialObjectInfo(BaseModel):
    """
    Image-space spatial interpretation of a detected object.
    Strictly 2D image coordinates — no physical distance or depth inferred.
    """

    label: str
    conf: float
    bbox: BoundingBox
    horizontal_zone: HorizontalZone
    vertical_zone: VerticalZone
    is_central: bool = Field(..., description="Whether object is in central view")
    is_prominent: bool = Field(..., description="Whether object occupies a significant area")
    relative_positions: list[str] = Field(default_factory=list, description="Relative position descriptions")
    overlapping_labels: list[str] = Field(default_factory=list, description="Labels of overlapping objects")


class SpatialAnalysis(BaseModel):
    """Result of deterministic image-space spatial reasoning."""

    frame_id: str
    objects: list[SpatialObjectInfo] = Field(default_factory=list)
    central_objects: list[SpatialObjectInfo] = Field(default_factory=list)
    prominent_objects: list[SpatialObjectInfo] = Field(default_factory=list)
    scene_label: str = "general"
    scene_description: Optional[str] = None
    uncertainties: list[str] = Field(default_factory=list)


# ── Context Reasoning Models ──────────────────────────────────────────────────

class ContextAnalysis(BaseModel):
    """
    Temporal and multi-frame context reasoning output.
    Conservative observation tracking across frames.
    """

    is_multi_frame: bool = False
    frame_count: int = 1
    persistent_objects: list[str] = Field(default_factory=list, description="Objects observed across multiple frames")
    new_objects: list[str] = Field(default_factory=list, description="Objects newly observed in latest frame")
    central_persistence: list[str] = Field(default_factory=list, description="Objects consistently in central view")
    repeated_hazards: list[str] = Field(default_factory=list, description="Hazards reported across observations")
    changes: list[str] = Field(default_factory=list, description="Notable visual changes between frames")


# ── Priority & Risk Models ────────────────────────────────────────────────────

class PriorityLevel(str, Enum):
    """Finite priority levels for assistive guidance."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PrioritizedItem(BaseModel):
    """An observation rated for relevance to user navigation assistance."""

    item: str
    priority: PriorityLevel
    reason: str
    is_hazard: bool = False


# ── Assistance Decision & Track 2 Result ──────────────────────────────────────

class AssistanceCategory(str, Enum):
    """Actionable category for Track 3 interpretation."""
    ALERT = "alert"         # Potential obstacle or hazard requiring user awareness
    GUIDANCE = "guidance"   # Relevant directional scene object (e.g. door, sign, walkway)
    INFO = "info"           # General scene context or background awareness
    NONE = "none"           # No actionable information to surface


class AssistanceDecision(BaseModel):
    """
    Structured assistance recommendation produced by Track 2.
    Does NOT produce spoken text or commands.
    """

    category: AssistanceCategory
    priority: PriorityLevel
    message: str = Field(..., description="Concise machine-readable summary for Track 3")
    relevant_items: list[PrioritizedItem] = Field(default_factory=list)


class Track2Result(BaseModel):
    """
    Final structured result exported by Track 2 to Track 3.
    """

    frame_id: str
    timestamp_ms: int
    decision: AssistanceDecision
    perception: PerceptionResult
    spatial: SpatialAnalysis
    context: ContextAnalysis
    summary: str
