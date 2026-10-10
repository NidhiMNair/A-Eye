# Data Conventions & Dataset Guidelines

This document specifies dataset naming, directory conventions, annotation formats, and protection policies for Track 1 Perception.

---

## 1. Data Directory Structure

Dataset contents under `track1_perception/data/` are ignored by Git (`data/*` rule in `.gitignore`), while `data/README.md` and `data/.gitkeep` remain tracked to preserve directory structure.

```text
track1_perception/data/
├── README.md                   # Tracked documentation
├── .gitkeep                    # Tracked placeholder
├── raw/                        # Gitignored raw recordings
│   ├── 20261012_corridorA_01/
│   │   ├── raw_video.mp4
│   │   ├── manifest.csv
│   │   ├── frames/
│   │   │   ├── frame_0000.jpg
│   │   │   ├── frame_0001.jpg
│   │   │   └── ...
│   │   └── annotations/
│   │       ├── frame_0000.txt   # YOLO format
│   │       ├── frame_0001.txt
│   │       └── coco_annotations.json # Optional COCO format
│   └── ...
└── splits/                     # Gitignored split manifests
    ├── train_manifest.csv
    ├── val_manifest.csv
    └── test_manifest.csv
```

---

## 2. Session ID Format

Every recording represents **one session**.

- **Convention**: `<YYYYMMDD>_<location>_<NN>`
- **Example**: `20261012_corridorA_01`, `20261015_staircaseB_02`
- **Regex Validation**: `^\d{8}_[a-zA-Z0-9]+_\d{2}$`
- **Rule**: All frames extracted from the same recording share the same Session ID. Frames belonging to a session MUST remain strictly grouped together during dataset splitting.

---

## 3. Annotation Conventions

### Internal Format (YOLO `.txt`)
- One text file per frame (e.g., `frame_0000.txt`).
- One object per line: `<class_id> <x_center> <y_center> <width> <height>`
- All coordinates normalized in `[0.0, 1.0]` relative to frame dimensions.
- Class IDs map directly to `configs/detector_labels.yaml`.

### Secondary Format (COCO `.json`)
- Standard COCO annotation format with `images`, `annotations`, and `categories`.
- Bounding box format in COCO: `[x_min_px, y_min_px, width_px, height_px]` in absolute pixels.

---

## 4. Test Set Protection Policy

To avoid data leakage and premature overfitting to test data:

1. **Splitting**: Splitting is executed **only by Session ID**, never by frame.
2. **Manifest Isolation**: Test split manifests are saved to `splits/test_manifest.csv`.
3. **Data Loader Safeguard**: The pipeline loader helper `load_split(split_name, allow_test=False)` explicitly raises a `PermissionError` if `split_name="test"` is requested without passing `allow_test=True`.
4. **Training Script Restriction**: All model training and parameter tuning scripts must consume **only** `train` and `val` splits.

---

## 5. Zero-Leakage Guarantee

The split utility executes an automated leakage check:
- Asserts that `Set(Sessions(Train)) ∩ Set(Sessions(Val)) = empty_set`
- Asserts that `Set(Sessions(Train)) ∩ Set(Sessions(Test)) = empty_set`
- Asserts that `Set(Sessions(Val)) ∩ Set(Sessions(Test)) = empty_set`
- Asserts that no frame file path is duplicated across any manifest split.
- Raises a hard error (non-zero exit code) if any leakage is detected.
