"""
track2/tests/test_vlm.py
==========================
Tests for VLM abstraction, MockVLM, and GeminiVLM error handling.

All tests in this file run 100% offline without network calls or API keys.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from track2.models import BoundingBox, DetectedObject, Frame, FrameBatch, PerceptionResult
from track2.vlm import (
    GeminiAPIKeyError,
    GeminiModelUnavailableError,
    GeminiNetworkError,
    GeminiRateLimitError,
    GeminiResponseError,
    GeminiVLM,
    MockVLM,
    VisionLanguageModel,
)


# ── Frame & FrameBatch Tests ──────────────────────────────────────────────────

def test_frame_creation_and_accessors():
    """Verify Frame fields and accessors."""
    frame = Frame(frame_id="f_001", timestamp=1000, data=b"fake_image_bytes")
    assert frame.frame_id == "f_001"
    assert frame.timestamp == 1000
    assert frame.data == b"fake_image_bytes"
    assert frame.image == b"fake_image_bytes"
    assert frame.timestamp_ms == 1000


def test_frame_validation_rejects_invalid_inputs():
    """Verify Frame rejects invalid IDs, negative timestamps, and empty data."""
    with pytest.raises(ValueError):
        Frame(frame_id="", timestamp=100, data=b"data")

    with pytest.raises(ValueError):
        Frame(frame_id="f", timestamp=-10, data=b"data")

    with pytest.raises(ValueError):
        Frame(frame_id="f", timestamp=100, data=b"")


def test_frame_batch_variable_size_and_ordering():
    """Verify FrameBatch preserves order and supports variable sizes."""
    f1 = Frame("f1", 100, b"data1")
    f2 = Frame("f2", 133, b"data2")
    f3 = Frame("f3", 166, b"data3")

    batch = FrameBatch([f1, f2, f3])
    assert len(batch) == 3
    assert batch[0] == f1
    assert batch[2] == f3
    assert batch.first_frame == f1
    assert batch.latest_frame == f3
    assert batch.frame_ids == ["f1", "f2", "f3"]


def test_frame_batch_rejects_empty_and_non_frames():
    """Verify FrameBatch rejects empty list and non-Frame items."""
    with pytest.raises(ValueError, match="at least one"):
        FrameBatch([])

    with pytest.raises(TypeError):
        FrameBatch([Frame("f1", 100, b"data"), "not_a_frame"])  # type: ignore[list-item]


# ── MockVLM Tests ─────────────────────────────────────────────────────────────

def test_mock_vlm_runs_offline_without_api_key():
    """Verify MockVLM executes offline returning structured PerceptionResult."""
    vlm = MockVLM()
    batch = FrameBatch([Frame("f_test", 1000, b"fake_pixels")])

    result = vlm.understand(batch)
    assert isinstance(result, PerceptionResult)
    assert result.frame_id == "f_test"
    assert result.timestamp_ms == 1000
    assert len(result.objects) > 0
    assert result.scene_description is not None
    assert result.scene_label == "indoor_corridor"


def test_mock_vlm_is_deterministic():
    """Verify MockVLM returns identical outputs for identical inputs."""
    vlm = MockVLM()
    batch = FrameBatch([Frame("f_det", 2000, b"bytes")])

    res1 = vlm.understand(batch)
    res2 = vlm.understand(batch)
    assert res1.model_dump() == res2.model_dump()


def test_mock_vlm_inherits_interface():
    """Verify MockVLM implements VisionLanguageModel."""
    assert issubclass(MockVLM, VisionLanguageModel)


# ── GeminiVLM Tests (Mocked Client) ───────────────────────────────────────────

def test_gemini_vlm_inherits_interface():
    """Verify GeminiVLM implements VisionLanguageModel."""
    assert issubclass(GeminiVLM, VisionLanguageModel)


def test_gemini_vlm_missing_api_key_raises():
    """Verify GeminiVLM raises GeminiAPIKeyError if key is missing."""
    with patch("track2.vlm.get_gemini_api_key", return_value=None):
        with pytest.raises(GeminiAPIKeyError, match="GEMINI_API_KEY is not configured"):
            GeminiVLM(api_key=None)


def test_gemini_vlm_empty_api_key_raises():
    """Verify GeminiVLM raises GeminiAPIKeyError if key is whitespace."""
    with pytest.raises(GeminiAPIKeyError):
        GeminiVLM(api_key="   ")


def test_gemini_vlm_default_and_custom_model():
    """Verify default model is gemini-3.8-flash and custom model parameter works."""
    mock_client = MagicMock()
    vlm_default = GeminiVLM(api_key="fake-key", client=mock_client)
    assert vlm_default.model == "gemini-3.8-flash"

    vlm_custom = GeminiVLM(api_key="fake-key", model="custom-model-id", client=mock_client)
    assert vlm_custom.model == "custom-model-id"


def test_gemini_vlm_handles_mocked_response():
    """Verify GeminiVLM parses structured output from SDK into PerceptionResult."""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "scene_label": "corridor",
        "scene_description": "A well-lit corridor with an open doorway ahead.",
        "objects": [
            {
                "label": "door",
                "conf": 0.95,
                "bbox": {"x_min": 0.35, "y_min": 0.1, "x_max": 0.65, "y_max": 0.9},
            }
        ],
        "spatial_relationships": ["Door is located centrally at the end of the walkway"],
        "hazards": [],
        "uncertainties": [],
    })
    mock_client.models.generate_content.return_value = mock_resp

    vlm = GeminiVLM(api_key="fake-key", client=mock_client)
    batch = FrameBatch([Frame("f_gem", 1000, b"\xff\xd8\xfffake_jpeg")])

    res = vlm.understand(batch)
    assert isinstance(res, PerceptionResult)
    assert res.frame_id == "f_gem"
    assert res.scene_label == "corridor"
    assert len(res.objects) == 1
    assert res.objects[0].label == "door"
    assert res.objects[0].bbox.x_min == 0.35


def test_gemini_vlm_api_error_handling():
    """Verify GeminiVLM maps API status codes to appropriate exceptions."""
    mock_client = MagicMock()
    vlm = GeminiVLM(api_key="fake-key", client=mock_client)
    batch = FrameBatch([Frame("f1", 100, b"\xff\xd8\xfffake")])

    # 401 Authentication failure
    exc_auth = Exception("API_KEY_INVALID")
    setattr(exc_auth, "code", 401)
    mock_client.models.generate_content.side_effect = exc_auth
    with pytest.raises(GeminiAPIKeyError):
        vlm.understand(batch)

    # 429 Rate limit
    exc_rate = Exception("RESOURCE_EXHAUSTED")
    setattr(exc_rate, "code", 429)
    mock_client.models.generate_content.side_effect = exc_rate
    with pytest.raises(GeminiRateLimitError):
        vlm.understand(batch)

    # 503 Model unavailable
    exc_unavail = Exception("503 UNAVAILABLE")
    setattr(exc_unavail, "code", 503)
    mock_client.models.generate_content.side_effect = exc_unavail
    with pytest.raises(GeminiModelUnavailableError):
        vlm.understand(batch)

    # Empty response
    mock_resp_empty = MagicMock()
    mock_resp_empty.text = ""
    mock_client.models.generate_content.side_effect = None
    mock_client.models.generate_content.return_value = mock_resp_empty
    with pytest.raises(GeminiResponseError):
        vlm.understand(batch)

    # Malformed JSON response
    mock_resp_bad = MagicMock()
    mock_resp_bad.text = "{invalid json"
    mock_client.models.generate_content.return_value = mock_resp_bad
    with pytest.raises(GeminiResponseError):
        vlm.understand(batch)
