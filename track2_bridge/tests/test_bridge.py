"""
track2_bridge/tests/test_bridge.py
==================================
Integration tests for the Track 2 Python bridge service.
All tests execute 100% offline using Track 2's MockVLM.
"""

from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient

from track2.vlm import GeminiAPIKeyError
from track2_bridge.server import app, create_pipeline


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "a-eye-track2-bridge"
    assert "vlm_mode" in data
    assert data["track2_available"] is True


def test_session_reset(client: TestClient) -> None:
    response = client.post("/session/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reset successfully" in data["message"]


def test_process_frames_single_frame(client: TestClient) -> None:
    # 1x1 dummy JPEG header bytes
    fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xd9"
    files = {"files": ("test_frame.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
    data = {"frame_id": "test_frame_001", "timestamp_ms": 1700000000000}

    response = client.post("/process-frames", files=files, data=data)
    assert response.status_code == 200
    result = response.json()

    assert result["frame_id"] == "test_frame_001"
    assert result["timestamp_ms"] == 1700000000000
    assert "decision" in result
    assert "category" in result["decision"]
    assert "priority" in result["decision"]
    assert "message" in result["decision"]
    assert "relevant_items" in result["decision"]
    assert "spatial" in result
    assert "context" in result
    assert "summary" in result


def test_process_frames_multi_frame_batch(client: TestClient) -> None:
    fake_jpeg1 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9"
    fake_jpeg2 = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9"
    files = [
        ("files", ("frame1.jpg", io.BytesIO(fake_jpeg1), "image/jpeg")),
        ("files", ("frame2.jpg", io.BytesIO(fake_jpeg2), "image/jpeg")),
    ]

    response = client.post("/process-frames", files=files)
    assert response.status_code == 200
    result = response.json()
    assert "decision" in result
    assert result["context"]["is_multi_frame"] is True


def test_process_frames_no_files_returns_400(client: TestClient) -> None:
    response = client.post("/process-frames")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "NO_FRAMES_PROVIDED"


def test_process_frames_empty_file_returns_400(client: TestClient) -> None:
    files = {"files": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    response = client.post("/process-frames", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "EMPTY_IMAGE_DATA"


def test_live_mode_without_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(GeminiAPIKeyError):
        create_pipeline(mode="live")
