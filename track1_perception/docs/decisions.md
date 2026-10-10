# Architectural & System Decisions Log

This document tracks all design decisions, platform targets, model choices, and data protocols across Track 1.

| Decision ID | Decision Topic | Status | Notes / Rationale |
| :--- | :--- | :--- | :--- |
| **DEC-001** | Target phone platform & deployment framework | Unresolved | Android (TFLite / ONNX Runtime Mobile) vs iOS (CoreML) subject to Track 3 app choices. |
| **DEC-002** | Final detector architecture | Proposed | Baseline set to Ultralytics YOLO (Nano/Small). Evaluation against SSD-MobileNet / EfficientDet pending. |
| **DEC-003** | Final OCR engine | Proposed | Multi-engine abstraction with EasyOCR / PaddleOCR baselines. Selection depends on latency & CER. |
| **DEC-004** | Final scene classification model | Proposed | MobileNetV3 / EfficientNet-Lite backbone fine-tuned on indoor/outdoor spatial datasets. |
| **DEC-005** | Tracking algorithm selection | Proposed | SORT-style IoU matching with Kalman/constant-velocity smoothing. |
| **DEC-006** | Final obstacle & scene categories | Unresolved | Baseline classes defined in `configs/detector_labels.yaml` & `scene_labels.yaml`; pending user testing feedback. |
| **DEC-007** | Dataset recording protocol & annotation format | Proposed | Session-based raw format with YOLO txt default & bi-directional COCO JSON conversion. |
| **DEC-008** | Agreed contract version | Proposed | Set to `CONTRACT_VERSION = "0.1-draft"` in `aeye_perception.contract`. |
| **DEC-009** | Single-camera distance estimation method | Unresolved | Physical distance from single 2D camera frames is unsafe without depth sensor/calibration; apparent image motion used instead. |
| **DEC-010** | Server VLM online response schema | Unresolved | Track 2 server VLM integration details pending. |
| **DEC-011** | Offline voice query routing | Unresolved | Handled by Track 3 connectivity manager. |
| **DEC-012** | On-device latency target | Unresolved | Target host machine measurements will be taken first; target phone hardware pending. |
| **DEC-013** | On-device quantization strategy | Proposed | INT8 / FP16 static & dynamic quantization via ONNX Runtime / PyTorch. |
| **DEC-014** | Handling unreliable VLM descriptions | Unresolved | Track 2 priority manager fallback behavior to be defined. |
| **DEC-015** | Session ID convention & splitting | Proposed | `<YYYYMMDD>_<location>_<NN>` naming. Session-only splitting with mandatory zero-leakage check. |
| **DEC-016** | Test set access protection | Proposed | `load_split()` helper enforces `allow_test=True` flag to read test manifest. |

> **Status Rules**:
> - **Confirmed**: Team-approved and locked requirement. (Requires explicit user confirmation).
> - **Proposed**: Current implementation baseline (can be replaced/configured).
> - **Unresolved**: Open decision requiring benchmarking or team alignment.
