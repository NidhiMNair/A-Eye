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

## Proposed Root README Pointer

To link Track 1 from the main repository `README.md`, append the following line to the root `README.md`:

```markdown
- **Track 1 Perception**: See [`track1_perception/README.md`](track1_perception/README.md) for perception pipeline code, models, contracts, and benchmark documentation.
```
