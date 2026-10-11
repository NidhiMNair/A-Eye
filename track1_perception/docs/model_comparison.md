# Object Detector Model Comparison & Trade-off Analysis

This document provides a comparative architectural review of lightweight object detector candidates for Track 1 Perception.

> **Status**: Proposed baseline set to **YOLOv8 Nano**.
> **Note**: Measured accuracy, mAP, and latency figures are host-machine estimates until real hardware benchmarks are executed in WP1.4.

---

## 1. Candidate Comparison Matrix

| Model Architecture | Parameter Count | Estimated File Size | Target Host Latency (CPU) | Primary Strengths | Licensing & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOv8 Nano (yolov8n)** | ~3.2M | ~6.2 MB | ~15-30 ms | High mAP@0.5, robust PyTorch & ONNX export pipeline | **AGPL-3.0**: Commercial use requires open-sourcing or commercial license. |
| **YOLOv8 Small (yolov8s)** | ~11.2M | ~22.5 MB | ~40-70 ms | Higher precision on small/occluded objects | **AGPL-3.0**: Heavier CPU footprint. |
| **SSD-MobileNetV3 Large** | ~5.4M | ~11.0 MB | ~20-35 ms | Permissive license, widely supported in TFLite / OpenCV DNN | **Apache 2.0**: Lower mAP on complex indoor occlusions compared to YOLO. |
| **EfficientDet-Lite0** | ~3.2M | ~7.0 MB | ~25-40 ms | Optimized for mobile TFLite edge deployment | **Apache 2.0**: PyTorch export tooling less flexible than YOLO. |
| **RT-DETR Nano** | ~4.8M | ~10.0 MB | ~30-50 ms | Transformer-based end-to-end detection, NMS-free | **Apache 2.0**: Higher memory bandwidth requirement on low-end CPUs. |

---

## 2. Licensing Considerations

- **Ultralytics YOLO (v8 / v11)**: Released under **AGPL-3.0**. If the end application is distributed commercially or served as a cloud service without releasing source code, dual commercial licensing from Ultralytics is required.
- **Torchvision / torchvision.models.detection**: Released under **BSD-3-Clause** / **Apache 2.0**.
- **MediaPipe / TFLite Models**: Released under **Apache 2.0**.

---

## 3. Deployment & Trade-off Evaluation

- **CPU Host Testing**: YOLOv8 Nano provides the best balance of setup speed, pre-trained weights, and ONNX exportability for initial Track 1 prototyping.
- **Mobile Edge Target**: Final selection between YOLO ONNX Runtime Mobile vs. MobileNetV3 TFLite will be made after WP1.4 export and quantization host benchmarks are completed.
