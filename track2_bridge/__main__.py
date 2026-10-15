"""
track2_bridge/__main__.py
=========================
CLI entry point for running the Track 2 Python bridge server.

Usage:
  python -m track2_bridge
"""

import uvicorn
from track2_bridge.config import get_bridge_host, get_bridge_port

if __name__ == "__main__":
    host = get_bridge_host()
    port = get_bridge_port()
    print(f"Starting A-Eye Track 2 Bridge on http://{host}:{port}")
    uvicorn.run("track2_bridge.server:app", host=host, port=port, reload=False)
