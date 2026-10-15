"""
track2_bridge/config.py
=======================
Configuration settings for the Track 2 Python bridge service.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

# Discover .env from root or track2/
try:
    from dotenv import load_dotenv

    _root_dir = Path(__file__).resolve().parent.parent
    for _candidate in [_root_dir / ".env", _root_dir / "track2" / ".env", Path(".env")]:
        if _candidate.is_file():
            load_dotenv(dotenv_path=_candidate, override=False)
            break
except ImportError:
    pass

VlmMode = Literal["mock", "live"]


def get_vlm_mode() -> VlmMode:
    """
    Get configured VLM mode from A_EYE_VLM_MODE environment variable.
    Defaults to 'mock' for safe offline development.
    """
    mode = os.environ.get("A_EYE_VLM_MODE", "mock").strip().lower()
    if mode in ("live", "gemini"):
        return "live"
    return "mock"


def get_bridge_host() -> str:
    """Host address to bind the bridge server to (default: 0.0.0.0)."""
    return os.environ.get("A_EYE_BRIDGE_HOST", "0.0.0.0")


def get_bridge_port() -> int:
    """Port to bind the bridge server to (default: 5000)."""
    val = os.environ.get("A_EYE_BRIDGE_PORT", "5000").strip()
    try:
        return int(val)
    except ValueError:
        return 5000
