"""
track2_bridge package
=====================
FastAPI HTTP bridge between mobile Track 3 client and Python Track 2 pipeline.
"""

from track2_bridge.config import get_bridge_host, get_bridge_port, get_vlm_mode

__all__ = ["get_vlm_mode", "get_bridge_host", "get_bridge_port"]
