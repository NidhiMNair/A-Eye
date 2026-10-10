"""
track2/vlm.py
==============
Vision-Language Model abstractions and implementations for Track 2.

Contains:
  - VisionLanguageModel (ABC)
  - MockVLM (offline deterministic mock)
  - GeminiVLM (Google Gemini SDK integration)
  - Gemini exception hierarchy
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from track2.config import get_gemini_api_key, get_gemini_model
from track2.models import (
    BoundingBox,
    DetectedObject,
    Frame,
    FrameBatch,
    PerceptionResult,
)

# Optional import of google-genai SDK
try:
    from google import genai
    from google.genai import errors, types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    genai = None  # type: ignore[assignment]
    errors = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


# ── Exception Hierarchy ───────────────────────────────────────────────────────

class GeminiVLMError(Exception):
    """Base exception for Gemini VLM operations."""
    pass


class GeminiAPIKeyError(GeminiVLMError, ValueError):
    """Raised when the Gemini API key is missing, empty, or rejected."""
    pass


class GeminiModelUnavailableError(GeminiVLMError):
    """Raised when the specified Gemini model is unavailable or not found."""
    pass


class GeminiRateLimitError(GeminiVLMError):
    """Raised when API rate limits or quota are exceeded."""
    pass


class GeminiNetworkError(GeminiVLMError):
    """Raised when network, connection, or timeout issues occur."""
    pass


class GeminiResponseError(GeminiVLMError):
    """Raised when the model returns an empty, corrupted, or malformed response."""
    pass


# ── Abstract VLM Interface ────────────────────────────────────────────────────

class VisionLanguageModel(ABC):
    """
    Abstract interface for Vision-Language Models in Track 2.

    Provider-agnostic interface exposing understand(frame_batch).
    """

    @abstractmethod
    def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
        """
        Process a FrameBatch and return structured scene observations.

        Args:
            frame_batch: A validated FrameBatch containing one or more Frame objects.

        Returns:
            PerceptionResult containing structured scene-understanding data.
        """
        raise NotImplementedError


# Clean aliases
VLMInterface = VisionLanguageModel
VLM = VisionLanguageModel


# ── Mock VLM Implementation ───────────────────────────────────────────────────

class MockVLM(VisionLanguageModel):
    """
    Deterministic mock VLM for offline tests and development.
    Requires no internet connection, API keys, or machine learning models.
    """

    def __init__(
        self,
        default_objects: Optional[Sequence[DetectedObject]] = None,
        default_scene_label: str = "indoor_corridor",
        default_scene_description: Optional[str] = "Indoor hallway with a chair and a person ahead.",
        default_hazards: Optional[list[str]] = None,
    ) -> None:
        if default_objects is not None:
            self._default_objects = list(default_objects)
        else:
            self._default_objects = [
                DetectedObject(
                    label="chair",
                    conf=0.92,
                    bbox=BoundingBox(x_min=0.30, y_min=0.40, x_max=0.70, y_max=0.90),
                ),
                DetectedObject(
                    label="person",
                    conf=0.88,
                    bbox=BoundingBox(x_min=0.60, y_min=0.10, x_max=0.90, y_max=0.80),
                ),
            ]
        self._default_scene_label = default_scene_label
        self._default_scene_description = default_scene_description
        self._default_hazards = default_hazards if default_hazards is not None else ["Chair in center walkway"]

    def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
        """Process FrameBatch and return deterministic structured PerceptionResult."""
        if not isinstance(frame_batch, FrameBatch):
            raise TypeError(
                f"understand() expected a FrameBatch instance, got {type(frame_batch).__name__}"
            )

        if len(frame_batch) == 0:
            raise ValueError("frame_batch cannot be empty")

        latest = frame_batch.latest_frame
        frame_id = latest.frame_id
        timestamp_ms = latest.timestamp_ms

        objects = [
            DetectedObject(
                label=obj.label,
                conf=obj.conf,
                bbox=BoundingBox(
                    x_min=obj.bbox.x_min,
                    y_min=obj.bbox.y_min,
                    x_max=obj.bbox.x_max,
                    y_max=obj.bbox.y_max,
                ),
                track_id=obj.track_id,
            )
            for obj in self._default_objects
        ]

        return PerceptionResult(
            frame_id=frame_id,
            timestamp_ms=timestamp_ms,
            source="offline_mock",
            objects=objects,
            scene_label=self._default_scene_label,
            scene_description=self._default_scene_description,
            spatial_relationships=["Chair is directly ahead in the center"],
            hazards=list(self._default_hazards),
            uncertainties=["Monocular perspective: distance cannot be precisely measured"],
        )


# ── Structured Schema for Gemini SDK ──────────────────────────────────────────

class _GeminiBoundingBox(BaseModel):
    x_min: float = Field(default=0.0, description="Normalized left edge [0.0, 1.0]")
    y_min: float = Field(default=0.0, description="Normalized top edge [0.0, 1.0]")
    x_max: float = Field(default=1.0, description="Normalized right edge [0.0, 1.0]")
    y_max: float = Field(default=1.0, description="Normalized bottom edge [0.0, 1.0]")


class _GeminiDetectedObject(BaseModel):
    label: str = Field(description="Object class name (e.g., 'chair', 'person', 'door')")
    conf: float = Field(default=0.9, description="Confidence score between 0.0 and 1.0")
    bbox: _GeminiBoundingBox = Field(
        default_factory=_GeminiBoundingBox,
        description="Normalized bounding box [x_min, y_min, x_max, y_max]",
    )


class _GeminiSceneUnderstanding(BaseModel):
    scene_label: str = Field(default="general", description="Coarse category for the scene")
    scene_description: str = Field(description="Concise description of the visible scene")
    objects: list[_GeminiDetectedObject] = Field(default_factory=list, description="Visible objects")
    spatial_relationships: list[str] = Field(default_factory=list, description="Spatial relationships")
    hazards: list[str] = Field(default_factory=list, description="Supported obstacles or hazards")
    uncertainties: list[str] = Field(default_factory=list, description="Visual uncertainties or limitations")


ASSISTIVE_VISION_SYSTEM_PROMPT = (
    "You are an assistive vision and navigation system for a visually impaired user. "
    "Analyze the supplied camera frame(s) in chronological order. "
    "Provide structured scene understanding data:\n"
    "1. A concise, practical description of the visible scene.\n"
    "2. Relevant visible objects, their labels, confidence, and approximate normalized bounding boxes.\n"
    "3. Key spatial relationships between objects relative to the camera viewpoint.\n"
    "4. Potential obstacles or hazards visibly supported by the images.\n"
    "5. Any visual uncertainties or limitations when something cannot be determined reliably.\n\n"
    "IMPORTANT SAFETY GUIDELINES:\n"
    "- Do NOT invent exact physical distances (e.g. '2.4 meters away'). Use qualitative terms.\n"
    "- Do NOT claim that an area or object is definitively safe to approach.\n"
    "- Do NOT present uncertain visual observations as established facts."
)


# ── Gemini VLM Implementation ─────────────────────────────────────────────────

class GeminiVLM(VisionLanguageModel):
    """
    Real Gemini Vision-Language Model implementation using google-genai SDK.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
    ) -> None:
        if not _GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package is not installed. "
                "Please install it with: pip install google-genai"
            )

        resolved_key = api_key if api_key is not None else get_gemini_api_key()
        if not resolved_key or not resolved_key.strip():
            raise GeminiAPIKeyError(
                "GEMINI_API_KEY is not configured. "
                "Please set GEMINI_API_KEY in track2/.env or environment variables."
            )

        self._api_key = resolved_key.strip()
        self._model = (model if model is not None else get_gemini_model()).strip()

        if client is not None:
            self._client = client
        else:
            self._client = genai.Client(api_key=self._api_key)

    @property
    def model(self) -> str:
        return self._model

    def understand(self, frame_batch: FrameBatch) -> PerceptionResult:
        """Send FrameBatch to Gemini and return validated PerceptionResult."""
        if not isinstance(frame_batch, FrameBatch):
            raise TypeError(
                f"understand() expected a FrameBatch instance, got {type(frame_batch).__name__}"
            )

        if len(frame_batch) == 0:
            raise ValueError("FrameBatch cannot be empty")

        parts = [self._frame_to_part(frame) for frame in frame_batch]

        contents: list[Any] = []
        if len(parts) == 1:
            contents.append(parts[0])
        else:
            for idx, (frame, part) in enumerate(zip(frame_batch, parts)):
                contents.append(f"Frame {idx + 1} (timestamp {frame.timestamp}):")
                contents.append(part)

        contents.append(ASSISTIVE_VISION_SYSTEM_PROMPT)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_GeminiSceneUnderstanding,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            self._handle_api_exception(exc)

        if not response or not hasattr(response, "text") or not response.text:
            raise GeminiResponseError("Gemini API returned an empty response.")

        return self._parse_and_validate_response(response.text, frame_batch)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _frame_to_part(self, frame: Frame) -> Any:
        raw_bytes: bytes
        mime_type = "image/jpeg"
        data = frame.data

        if isinstance(data, (bytes, bytearray, memoryview)):
            raw_bytes = bytes(data)
            detected_mime = self._detect_mime_type(raw_bytes)
            if detected_mime:
                mime_type = detected_mime
        elif isinstance(data, (str, Path, os.PathLike)):
            path = Path(data)
            if not path.is_file():
                raise ValueError(
                    f"Frame '{frame.frame_id}' image path does not exist: {path}"
                )
            raw_bytes = path.read_bytes()
            guessed_mime, _ = mimetypes.guess_type(str(path))
            if guessed_mime:
                mime_type = guessed_mime
            else:
                detected_mime = self._detect_mime_type(raw_bytes)
                if detected_mime:
                    mime_type = detected_mime
        else:
            raise ValueError(
                f"Unsupported image data format for frame '{frame.frame_id}': {type(data).__name__}. "
                "Expected bytes, bytearray, or a file path."
            )

        return types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)

    @staticmethod
    def _detect_mime_type(data: bytes) -> Optional[str]:
        if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        if len(data) >= 6 and (data[:6] == b"GIF87a" or data[:6] == b"GIF89a"):
            return "image/gif"
        return None

    def _parse_and_validate_response(
        self,
        response_text: str,
        frame_batch: FrameBatch,
    ) -> PerceptionResult:
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError as err:
            raise GeminiResponseError(
                f"Failed to decode Gemini structured JSON response: {err}"
            ) from err

        try:
            scene = _GeminiSceneUnderstanding.model_validate(parsed_data)
        except Exception as err:
            raise GeminiResponseError(
                f"Gemini response did not match expected structured schema: {err}"
            ) from err

        latest_frame = frame_batch.latest_frame
        detected_objects: list[DetectedObject] = []

        for obj in scene.objects:
            clamped_bbox = self._sanitize_bounding_box(obj.bbox)
            clamped_conf = max(0.0, min(1.0, float(obj.conf)))
            label = obj.label.strip() if obj.label.strip() else "object"

            detected_objects.append(
                DetectedObject(
                    label=label,
                    conf=clamped_conf,
                    bbox=clamped_bbox,
                    track_id=None,
                )
            )

        return PerceptionResult(
            frame_id=latest_frame.frame_id,
            timestamp_ms=latest_frame.timestamp_ms,
            source="online_gemini",
            objects=detected_objects,
            scene_label=scene.scene_label.strip() or "general",
            scene_description=scene.scene_description.strip(),
            spatial_relationships=scene.spatial_relationships,
            hazards=scene.hazards,
            uncertainties=scene.uncertainties,
        )

    @staticmethod
    def _sanitize_bounding_box(raw_box: _GeminiBoundingBox) -> BoundingBox:
        x_min = max(0.0, min(0.999, float(raw_box.x_min)))
        y_min = max(0.0, min(0.999, float(raw_box.y_min)))
        x_max = max(x_min + 0.001, min(1.0, float(raw_box.x_max)))
        y_max = max(y_min + 0.001, min(1.0, float(raw_box.y_max)))

        if x_min >= x_max:
            x_min = max(0.0, x_max - 0.01)
            if x_min >= x_max:
                x_max = min(1.0, x_min + 0.01)

        if y_min >= y_max:
            y_min = max(0.0, y_max - 0.01)
            if y_min >= y_max:
                y_max = min(1.0, y_min + 0.01)

        return BoundingBox(
            x_min=round(x_min, 4),
            y_min=round(y_min, 4),
            x_max=round(x_max, 4),
            y_max=round(y_max, 4),
        )

    def _handle_api_exception(self, exc: Exception) -> None:
        err_msg = str(exc)
        status_code = getattr(exc, "code", None)
        if status_code is None and hasattr(exc, "status_code"):
            status_code = getattr(exc, "status_code")

        if status_code in (401, 403) or "API_KEY_INVALID" in err_msg or "PERMISSION_DENIED" in err_msg:
            raise GeminiAPIKeyError(f"Gemini API authentication failed: {err_msg}") from exc

        if status_code == 429 or "RESOURCE_EXHAUSTED" in err_msg or "rate limit" in err_msg.lower():
            raise GeminiRateLimitError(f"Gemini API rate limit exceeded: {err_msg}") from exc

        if status_code in (404, 503) or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
            raise GeminiModelUnavailableError(f"Gemini model '{self._model}' is unavailable: {err_msg}") from exc

        type_name = type(exc).__name__.lower()
        if any(term in type_name for term in ("connect", "timeout", "network", "socket")):
            raise GeminiNetworkError(f"Network error communicating with Gemini API: {err_msg}") from exc

        raise GeminiVLMError(f"Gemini VLM request failed: {err_msg}") from exc
