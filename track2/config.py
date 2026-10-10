"""
track2/config.py
==================
Track 2 configuration and environment management.

Handles discovery of .env and loading of GEMINI_API_KEY and GEMINI_MODEL
without exposing secrets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Automatically discover and load .env if python-dotenv is present
try:
    from dotenv import load_dotenv

    _current_dir = Path(__file__).resolve().parent
    _env_candidates = [
        _current_dir / ".env",
        _current_dir.parent / ".env",
        Path(".env"),
        Path("track2/.env"),
    ]
    for _candidate in _env_candidates:
        if _candidate.is_file():
            load_dotenv(dotenv_path=_candidate, override=False)
            break
except ImportError:
    pass

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def get_gemini_api_key() -> Optional[str]:
    """Retrieve GEMINI_API_KEY from environment without logging or printing."""
    return os.environ.get("GEMINI_API_KEY")


def get_gemini_model() -> str:
    """Retrieve GEMINI_MODEL from environment (defaults to gemini-3.8-flash)."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
