# Track 1 – Perception Subsystem (A-Eye)

> **Important Assistive System Disclaimer**:
> A-Eye is designed as a smartphone-based AI navigation and assistance system to enhance environmental awareness for visually impaired users.
> It is an **assistive aid** and **NOT** a replacement for primary mobility tools such as a white cane, guide dog, or formal mobility training.
> Apparent image motion (`dx`, `dy`, `growth`) describes 2D bounding box changes in normalized frame coordinates and **does not** represent physical 3D velocity or absolute collision risk.

---

## Overview

The `track1_perception` package processes camera video frames to produce structured perception data (`PerceptionResult`).

### Key Work Packages
- **WP1.1 Obstacle Detection**: Lightweight detector returning normalized bounding boxes and object classes.
- **WP1.2 Scene Recognition**: Scene classifier identifying macro environment labels (corridor, staircase, room, outdoor path, unknown).
- **WP1.3 OCR / Text Recognition**: Text detector & recognizer for signs, room numbers, and notices.
- **WP1.4 Runtime & On-Device Optimization**: `perceive()` interface, timing breakdown, model export (ONNX/quantization).
- **WP1.5 Object Tracking & Motion**: Tracker assigning persistent `track_id`s and estimating 2D apparent motion (`dx`, `dy`, `growth`).
- **WP1.6 Data Tooling & Benchmarking**: Video frame extraction, dataset conversion, session-based splitting (zero-leakage), and evaluation benchmark runners.

---

## Directory Structure

```text
track1_perception/
├── README.md                  # Track 1 documentation and guide
├── pyproject.toml             # Package setup and setuptools configuration
├── requirements.txt           # Lightweight core & dev dependencies
├── configs/                   # System configurations (YAML)
│   ├── default.yaml           # Pipeline settings & threshold defaults
│   ├── detector_labels.yaml   # Obstacle class labels
│   └── scene_labels.yaml      # Scene category labels
├── docs/                      # Architectural decisions and documentation
│   └── decisions.md           # Decisions tracking log
├── src/
│   └── aeye_perception/       # Core Python package
│       ├── __init__.py
│       ├── contract.py        # PerceptionResult schema (Pydantic v2)
│       └── geometry.py        # Bounding box & geometry utilities
├── fixtures/                  # Mock JSON schemas and test sample directories
│   ├── mock_perception_result.json
│   └── real_samples/          # User sample drop directory
├── scripts/                   # CLI utilities and synthetic data generators
│   ├── make_synthetic_fixtures.py
│   └── mock_stream.py
└── tests/                    # Unit tests (pytest)
    ├── test_contract.py
    └── test_geometry.py
```

---

## Quickstart & Installation

### 1. Setup Virtual Environment (Windows PowerShell)

```powershell
# Navigate to track1_perception directory
cd track1_perception

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 2. Install Package

```powershell
# Editable install with dev dependencies
pip install -e ".[dev]"
```

Alternatively, using `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 3. Run Tests

```powershell
pytest
```

---

## Video Perception Inference Pipeline

The video pipeline connects the object detector (`YOLOObstacleDetector` or `MockDetector`), the `IoUTracker`, and the shared `PerceptionResult` contract, outputting frame-by-frame perceptions to JSONL format and optionally writing an annotated video.

### Running the Pipeline

**1. Mock Mode (no model weights or GPU required):**
```powershell
python scripts/run_video_pipeline.py --video path/to/video.mp4 --mock --output-jsonl results.jsonl --output-video annotated.mp4
```

**2. YOLO Detector Mode:**
```powershell
python scripts/run_video_pipeline.py --video path/to/video.mp4 --weights models/yolov8n.pt --output-jsonl results.jsonl --output-video annotated.mp4
```

**Options:**
- `--video <path>`: Input video file (required).
- `--mock`: Use deterministic `MockDetector` for testing and synthetic verification without downloading weights.
- `--weights <path>`: YOLO weights checkpoint (default: `yolov8n.pt`).
- `--conf <float>`: Confidence threshold override (e.g., `0.40`).
- `--iou <float>`: Detector NMS IoU threshold override (e.g., `0.50`).
- `--output-jsonl <path>`: Save frame-by-frame `PerceptionResult` records as JSONL (one JSON object per line).
- `--output-video <path>`: Save MP4 video with rendered bounding boxes, class labels, and persistent track IDs.
- `--max-frames <int>`: Limit processing to the first N frames.

### Outputs & Timestamp Behavior
- **JSONL Output**: Each line is a valid, deserializable `PerceptionResult` record adhering to `CONTRACT_VERSION = "0.1-draft"`:
  - Monotonically increasing `frame_id` (0, 1, 2, ...).
  - `source="offline"`, empty `text_blocks=[]`, and `scene_description=None`.
  - Persistent `track_id` and apparent 2D motion vectors (`dx`, `dy`, `growth`).
- **Timestamp Handling**: Video container timestamps (`CAP_PROP_POS_MSEC`) are used when strictly increasing. If video metadata contains zero, duplicate, or backwards timestamps, the pipeline advances each frame timestamp by at least $\Delta t = \text{round}(1000 / \text{fps})$ ms, ensuring strictly increasing timestamps ($t_k > t_{k-1}$) for tracking stability.

---

## Proposed Root README Pointer

To link Track 1 from the main repository `README.md`, append the following line to the root `README.md`:

```markdown
- **Track 1 Perception**: See [`track1_perception/README.md`](track1_perception/README.md) for perception pipeline code, models, contracts, and benchmark documentation.
```
