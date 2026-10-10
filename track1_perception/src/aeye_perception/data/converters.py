"""
Annotation converters for dataset format translation.

Supports bi-directional conversion between COCO JSON and YOLO txt formats.
Class mappings are dynamically loaded from config files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union, Optional
import yaml

from aeye_perception.geometry import clamp_bbox

logger = logging.getLogger(__name__)


def load_class_labels(config_path: Union[str, Path]) -> Dict[int, str]:
    """
    Load class dictionary mapping integer ID to class name from detector_labels.yaml.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Label configuration file not found at {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    raw_classes = data.get("classes", {})
    # Convert string keys to integer keys if needed
    classes = {int(k): str(v) for kk, v in raw_classes.items() for k in [kk]}
    return classes


def coco_to_yolo(
    coco_json_path: Union[str, Path],
    output_yolo_dir: Union[str, Path],
    label_config_path: Union[str, Path],
) -> List[Path]:
    """
    Convert COCO JSON annotations to individual YOLO .txt format files.

    YOLO format per line: <class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
    """
    coco_path = Path(coco_json_path)
    output_dir = Path(output_yolo_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not coco_path.exists():
        raise FileNotFoundError(f"COCO JSON file not found at {coco_path}")

    with open(coco_path, "r") as f:
        coco_data = json.load(f)

    class_dict = load_class_labels(label_config_path)
    # Map category names to class IDs defined in label_config
    name_to_id = {name: cid for cid, name in class_dict.items()}

    # Map COCO category_id to internal class_id
    coco_cat_id_to_internal: Dict[int, int] = {}
    for cat in coco_data.get("categories", []):
        cat_name = cat.get("name")
        cat_id = cat.get("id")
        if cat_name in name_to_id:
            coco_cat_id_to_internal[cat_id] = name_to_id[cat_name]
        elif cat_id in class_dict:
            coco_cat_id_to_internal[cat_id] = cat_id
        else:
            logger.warning(f"Category '{cat_name}' (ID {cat_id}) not found in label config. Skipping.")

    images_map = {img["id"]: img for img in coco_data.get("images", [])}
    annotations_by_img: Dict[int, List[Dict[str, Any]]] = {}

    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        annotations_by_img.setdefault(img_id, []).append(ann)

    created_files = []

    for img_id, img_info in images_map.items():
        file_name = Path(img_info["file_name"]).stem + ".txt"
        txt_path = output_dir / file_name
        img_w = img_info.get("width")
        img_h = img_info.get("height")

        if not img_w or not img_h or img_w <= 0 or img_h <= 0:
            logger.error(f"Invalid dimensions for image {img_info.get('file_name')}: {img_w}x{img_h}")
            continue

        lines = []
        for ann in annotations_by_img.get(img_id, []):
            cat_id = ann.get("category_id")
            if cat_id not in coco_cat_id_to_internal:
                continue

            internal_class_id = coco_cat_id_to_internal[cat_id]
            # COCO bbox: [x_min, y_min, width, height] in pixels
            x_min, y_min, w_px, h_px = ann["bbox"]

            # Convert to normalized YOLO center format
            x_center = (x_min + w_px / 2.0) / img_w
            y_center = (y_min + h_px / 2.0) / img_h
            w_norm = w_px / img_w
            h_norm = h_px / img_h

            # Convert normalized center box to corner box for clamping
            x1 = x_center - w_norm / 2.0
            y1 = y_center - h_norm / 2.0
            x2 = x_center + w_norm / 2.0
            y2 = y_center + h_norm / 2.0

            clamped = clamp_bbox([x1, y1, x2, y2])
            cx = (clamped[0] + clamped[2]) / 2.0
            cy = (clamped[1] + clamped[3]) / 2.0
            wn = clamped[2] - clamped[0]
            hn = clamped[3] - clamped[1]

            lines.append(f"{internal_class_id} {cx:.6f} {cy:.6f} {wn:.6f} {hn:.6f}")

        with open(txt_path, "w") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))

        created_files.append(txt_path)

    logger.info(f"Converted COCO JSON to {len(created_files)} YOLO txt files in {output_dir}")
    return created_files


def yolo_to_coco(
    yolo_dir: Union[str, Path],
    images_info: List[Dict[str, Any]],
    output_coco_path: Union[str, Path],
    label_config_path: Union[str, Path],
) -> Path:
    """
    Convert a directory of YOLO .txt annotations to a single COCO JSON file.

    images_info: List of dicts containing image metadata:
                 [{ "id": 1, "file_name": "frame_0001.jpg", "width": 640, "height": 480 }, ...]
    """
    yolo_path_dir = Path(yolo_dir)
    output_path = Path(output_coco_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    class_dict = load_class_labels(label_config_path)

    categories = [
        {"id": cid, "name": cname, "supercategory": "obstacle"}
        for cid, cname in sorted(class_dict.items())
    ]

    images = []
    annotations = []
    ann_id_counter = 1

    for img_meta in images_info:
        img_id = img_meta["id"]
        file_name = img_meta["file_name"]
        img_w = img_meta["width"]
        img_h = img_meta["height"]

        images.append({
            "id": img_id,
            "file_name": file_name,
            "width": img_w,
            "height": img_h,
        })

        stem = Path(file_name).stem
        txt_file = yolo_path_dir / f"{stem}.txt"

        if not txt_file.exists():
            continue

        with open(txt_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                logger.warning(f"Malformed line in {txt_file}: '{line}'")
                continue

            try:
                cat_id = int(parts[0])
                cx_n, cy_n, w_n, h_n = [float(p) for p in parts[1:]]
            except ValueError:
                logger.warning(f"Invalid numeric values in {txt_file}: '{line}'")
                continue

            if cat_id not in class_dict:
                logger.warning(f"Class ID {cat_id} in {txt_file} not in label config.")

            # Denormalize to pixel COCO bbox [x_min_px, y_min_px, width_px, height_px]
            w_px = round(w_n * img_w, 2)
            h_px = round(h_n * img_h, 2)
            x_min_px = round((cx_n - w_n / 2.0) * img_w, 2)
            y_min_px = round((cy_n - h_n / 2.0) * img_h, 2)
            area_px = round(w_px * h_px, 2)

            annotations.append({
                "id": ann_id_counter,
                "image_id": img_id,
                "category_id": cat_id,
                "bbox": [x_min_px, y_min_px, w_px, h_px],
                "area": area_px,
                "iscrowd": 0,
            })
            ann_id_counter += 1

    coco_structure = {
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }

    with open(output_path, "w") as f:
        json.dump(coco_structure, f, indent=2)

    logger.info(f"Converted YOLO annotations to COCO JSON at {output_path}")
    return output_path
