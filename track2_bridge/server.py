"""
track2_bridge/server.py
=======================
FastAPI HTTP bridge exposing Track 2 reasoning pipeline to mobile Track 3 clients.

Endpoints:
  - GET  /health          Healthcheck, active VLM mode (mock vs live), Track 2 status.
  - POST /process-frames  Multipart image frame(s) ingestion -> Track2Result JSON.
  - POST /session/reset   Resets temporal context history for a new user session.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from track2.config import get_gemini_api_key, get_gemini_model
from track2.models import Frame, FrameBatch, Track2Result
from track2.pipeline import Track2Pipeline
from track2.vlm import GeminiAPIKeyError, GeminiVLM, GeminiVLMError, MockVLM
from track2_bridge.config import get_vlm_mode

logger = logging.getLogger("track2_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def create_pipeline(mode: Optional[str] = None) -> tuple[Track2Pipeline, str]:
    """
    Initialize Track2Pipeline once based on configured VLM mode.
    Returns (pipeline, resolved_mode).
    """
    selected_mode = (mode or get_vlm_mode()).strip().lower()

    if selected_mode in ("live", "gemini"):
        api_key = get_gemini_api_key()
        if not api_key or not api_key.strip():
            logger.error("Live VLM mode requested, but GEMINI_API_KEY is not set.")
            raise GeminiAPIKeyError(
                "GEMINI_API_KEY is missing or empty. "
                "Set GEMINI_API_KEY in track2/.env or environment variables to use live mode."
            )
        vlm = GeminiVLM(api_key=api_key, model=get_gemini_model())
        logger.info("Track2Pipeline initialized in LIVE mode with model '%s'", vlm.model)
        return Track2Pipeline(vlm=vlm), "live"
    else:
        vlm = MockVLM()
        logger.info("Track2Pipeline initialized in MOCK mode (offline deterministic)")
        return Track2Pipeline(vlm=vlm), "mock"


# Initialize pipeline instance once at module level (persists context across session calls)
try:
    pipeline, active_vlm_mode = create_pipeline()
    pipeline_init_error: Optional[str] = None
except Exception as e:
    # If live mode fails on startup due to missing key, fallback to mock pipeline or record error
    logger.warning("Pipeline initialization with configured mode failed (%s). Falling back to mock.", e)
    pipeline = Track2Pipeline(vlm=MockVLM())
    active_vlm_mode = "mock"
    pipeline_init_error = str(e)


app = FastAPI(
    title="A-Eye Track 2 Bridge",
    description="Bridge connecting Track 3 mobile clients to Track 2 scene reasoning pipeline",
    version="1.0.0",
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Format unhandled exceptions into structured JSON responses."""
    logger.exception("Unhandled error processing request: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred in the bridge service.",
            "details": str(exc),
        },
    )


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Report health status, active VLM mode, and Track 2 availability.
    """
    return {
        "status": "healthy",
        "service": "a-eye-track2-bridge",
        "vlm_mode": active_vlm_mode,
        "track2_available": True,
        "init_warning": pipeline_init_error,
    }


@app.post("/session/reset")
async def reset_session() -> dict[str, Any]:
    """
    Reset Track 2 temporal context history for a fresh user session.
    """
    pipeline.reset_context()
    logger.info("Session context reset requested by Track 3 client.")
    return {
        "status": "success",
        "message": "Track 2 temporal context reset successfully.",
    }


@app.post("/process-frames")
async def process_frames(
    files: Optional[list[UploadFile]] = File(None),
    image: Optional[UploadFile] = File(None),
    frame_id: Optional[str] = Form(None),
    timestamp_ms: Optional[int] = Form(None),
) -> dict[str, Any]:
    """
    Process one or more chronological image frames through Track 2 pipeline.

    Accepts:
      - Multipart files under 'files' (list) or 'image' (single).
      - Optional metadata form fields 'frame_id', 'timestamp_ms'.

    Returns:
      Track2Result JSON serialized matching Track 2 contract.
    """
    # Gather incoming files
    resolved_uploads: list[UploadFile] = []
    if files:
        resolved_uploads.extend(files)
    if image and image not in resolved_uploads:
        resolved_uploads.append(image)

    if not resolved_uploads:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "NO_FRAMES_PROVIDED",
                "message": "No image frames received. Send frames using 'files' or 'image' form fields.",
            },
        )

    frames: list[Frame] = []
    current_time_ms = int(time.time() * 1000)

    for idx, upload in enumerate(resolved_uploads):
        content = await upload.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "EMPTY_IMAGE_DATA",
                    "message": f"Uploaded file '{upload.filename or idx}' is empty.",
                },
            )

        f_id = frame_id if (len(resolved_uploads) == 1 and frame_id) else f"{uuid4()}_{idx}"
        t_ms = (
            timestamp_ms
            if (len(resolved_uploads) == 1 and timestamp_ms is not None)
            else (current_time_ms + idx * 100)
        )

        try:
            frames.append(Frame(frame_id=f_id, timestamp=t_ms, data=content))
        except Exception as err:
            logger.error("Failed to construct Frame object: %s", err)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "FRAME_CONSTRUCTION_ERROR",
                    "message": f"Failed to construct valid Track 2 Frame: {err}",
                },
            ) from err

    try:
        batch = FrameBatch(frames)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_FRAME_BATCH",
                "message": f"Failed to create FrameBatch: {err}",
            },
        ) from err

    # Process through Track 2 pipeline
    try:
        start_time = time.perf_counter()
        result: Track2Result = pipeline.process(batch)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Processed FrameBatch (size %d) in %sms: Category=%s, Priority=%s",
            len(batch),
            elapsed_ms,
            result.decision.category.value,
            result.decision.priority.value,
        )
    except GeminiVLMError as vlm_err:
        logger.error("Track 2 VLM failure: %s", vlm_err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error_code": "VLM_ERROR",
                "message": "Vision-Language Model processing failed upstream.",
                "details": str(vlm_err),
            },
        ) from vlm_err
    except Exception as err:
        logger.exception("Track 2 pipeline processing failure: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PIPELINE_ERROR",
                "message": f"Track 2 pipeline execution error: {err}",
            },
        ) from err

    return result.model_dump(mode="json")
