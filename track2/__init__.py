"""
track2/__init__.py
====================
A-Eye Track 2 — Reasoning and Online Intelligence.

Complete processing pipeline from camera frames to structured assistance:
  FrameBatch
      ↓
  VLM (GeminiVLM or MockVLM)
      ↓
  PerceptionResult
      ↓
  SpatialReasoner (image-space)
      ↓
  ContextReasoner (temporal persistence)
      ↓
  AssistanceDecisionEngine (priority & assistance)
      ↓
  Track2Result
"""

from track2.config import get_gemini_api_key, get_gemini_model
from track2.context import ContextReasoner
from track2.decision import AssistanceDecisionEngine
from track2.models import (
    AssistanceCategory,
    AssistanceDecision,
    BoundingBox,
    ContextAnalysis,
    DetectedObject,
    Frame,
    FrameBatch,
    HorizontalZone,
    PerceptionResult,
    PrioritizedItem,
    PriorityLevel,
    SpatialAnalysis,
    SpatialObjectInfo,
    Track2Result,
    VerticalZone,
)
from track2.pipeline import Track2Pipeline
from track2.spatial import SpatialReasoner
from track2.vlm import (
    GeminiAPIKeyError,
    GeminiModelUnavailableError,
    GeminiNetworkError,
    GeminiRateLimitError,
    GeminiResponseError,
    GeminiVLM,
    GeminiVLMError,
    MockVLM,
    VisionLanguageModel,
    VLM,
    VLMInterface,
)

__all__ = [
    # Input
    "Frame",
    "FrameBatch",
    # Perception
    "BoundingBox",
    "DetectedObject",
    "PerceptionResult",
    # Spatial
    "HorizontalZone",
    "VerticalZone",
    "SpatialObjectInfo",
    "SpatialAnalysis",
    "SpatialReasoner",
    # Context
    "ContextAnalysis",
    "ContextReasoner",
    # Decision & Priority
    "PriorityLevel",
    "PrioritizedItem",
    "AssistanceCategory",
    "AssistanceDecision",
    "AssistanceDecisionEngine",
    # Pipeline
    "Track2Pipeline",
    "Track2Result",
    # VLM
    "VisionLanguageModel",
    "VLMInterface",
    "VLM",
    "MockVLM",
    "GeminiVLM",
    "GeminiVLMError",
    "GeminiAPIKeyError",
    "GeminiModelUnavailableError",
    "GeminiRateLimitError",
    "GeminiNetworkError",
    "GeminiResponseError",
    # Config
    "get_gemini_api_key",
    "get_gemini_model",
]
