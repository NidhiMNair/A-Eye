"""Integration test for Gemini VLM within Track 2.

Only runs when RUN_GEMINI_INTEGRATION="1" is explicitly set in the environment.
Otherwise, it is safely skipped so normal test runs are 100% offline.
"""

from __future__ import annotations

import os
import struct
import zlib
import pytest

from track2.models import Frame, FrameBatch, Track2Result
from track2.vlm import GeminiVLM, GeminiModelUnavailableError, GeminiRateLimitError
from track2.pipeline import Track2Pipeline
from track2.config import get_gemini_api_key


def _generate_valid_png_bytes(width: int = 64, height: int = 64, color: tuple[int, int, int] = (180, 120, 60)) -> bytes:
    """Generate a valid PNG image buffer using standard library without external dependencies."""
    raw_scanlines = bytearray()
    for _ in range(height):
        raw_scanlines.append(0)  # Filter byte: None
        for _ in range(width):
            raw_scanlines.extend(color)
    compressed = zlib.compress(bytes(raw_scanlines))

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png.extend(struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr)))
    png.extend(struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", zlib.crc32(b"IDAT" + compressed)))
    png.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND")))
    return bytes(png)


@pytest.mark.integration
def test_gemini_pipeline_live_integration():
    """Live end-to-end integration test with Gemini API."""
    if os.getenv("RUN_GEMINI_INTEGRATION") != "1":
        pytest.skip("Skipping live Gemini integration test (set RUN_GEMINI_INTEGRATION=1 to run)")

    api_key = get_gemini_api_key()
    if not api_key:
        pytest.skip("GEMINI_API_KEY is not set or empty")

    image_bytes = _generate_valid_png_bytes(width=64, height=64)

    frame = Frame(
        frame_id="integration_test_frame_01",
        timestamp_ms=1710000000000,
        image_data=image_bytes,
    )
    batch = FrameBatch(frames=[frame])

    vlm = GeminiVLM(api_key=api_key)
    pipeline = Track2Pipeline(vlm=vlm)

    try:
        result = pipeline.process(batch)
    except (GeminiModelUnavailableError, GeminiRateLimitError) as exc:
        pytest.skip(f"Gemini API endpoint temporarily unavailable (503/429): {exc}")

    assert isinstance(result, Track2Result)
    assert result.frame_id == "integration_test_frame_01"
    assert result.timestamp_ms == 1710000000000
    assert result.perception is not None
    assert isinstance(result.perception.scene_description, str)
    assert len(result.perception.scene_description) > 0
    assert result.spatial is not None
    assert result.context is not None
    assert result.decision is not None
