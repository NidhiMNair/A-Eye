"""
Session-based dataset splitting, leakage validation, and test set isolation.

Enforces zero data leakage between splits and protects test set privacy.
"""

import csv
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union, Optional, Any
import numpy as np
import yaml

logger = logging.getLogger(__name__)

SESSION_ID_PATTERN = re.compile(r"^\d{8}_[a-zA-Z0-9]+_\d{2}$")


def validate_session_id(session_id: str) -> bool:
    """Check if session ID matches convention <YYYYMMDD>_<location>_<NN>."""
    return bool(SESSION_ID_PATTERN.match(session_id))


def check_leakage(split_manifests: Dict[str, Union[str, Path]]) -> bool:
    """
    Assert zero session leakage and zero frame path leakage across dataset splits.

    Raises ValueError if any session ID or frame path appears in more than one split.
    """
    sessions_by_split: Dict[str, Set[str]] = {}
    frames_by_split: Dict[str, Set[str]] = {}

    for split_name, manifest_path in split_manifests.items():
        path = Path(manifest_path)
        if not path.exists():
            continue

        sessions: Set[str] = set()
        frames: Set[str] = set()

        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sess_id = row["session_id"]
                frame_p = row["frame_path"]
                sessions.add(sess_id)
                frames.add(frame_p)

        sessions_by_split[split_name] = sessions
        frames_by_split[split_name] = frames

    split_names = list(sessions_by_split.keys())
    leaks = []

    # Pairwise comparison
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]

            session_overlap = sessions_by_split[s1].intersection(sessions_by_split[s2])
            if session_overlap:
                leaks.append(f"Session leakage between {s1} and {s2}: {session_overlap}")

            frame_overlap = frames_by_split[s1].intersection(frames_by_split[s2])
            if frame_overlap:
                leaks.append(f"Frame path leakage between {s1} and {s2}: {frame_overlap}")

    if leaks:
        error_msg = "DATA LEAKAGE DETECTED!\n" + "\n".join(leaks)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Leakage check PASSED: Zero session and frame path overlap across splits.")
    return True


def load_split(
    split_name: str,
    manifests_dir: Union[str, Path],
    allow_test: bool = False,
) -> List[Dict[str, str]]:
    """
    Load rows from split manifest CSV.

    PROTECTION SAFEGUARD: Refuses to load the 'test' split unless allow_test=True is passed.
    """
    split_name = split_name.lower().strip()
    if split_name == "test" and not allow_test:
        raise PermissionError(
            "Access to the 'test' split manifest is restricted! "
            "Pass allow_test=True explicitly to confirm intentional test evaluation."
        )

    manifest_path = Path(manifests_dir) / f"{split_name}_manifest.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file for split '{split_name}' not found at {manifest_path}")

    rows = []
    with open(manifest_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))

    return rows


def split_dataset(
    sessions: List[Dict[str, Any]],
    output_dir: Union[str, Path],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    stratify: bool = False,
    label_config_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Path]:
    """
    Split sessions into reproducible train/val/test splits BY SESSION ONLY.

    sessions: List of session dicts:
              [{ "session_id": "20261012_corridorA_01", "manifest_rows": [...] }, ...]
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if len(sessions) < 3:
        raise ValueError(
            f"Dataset splitting requires at least 3 sessions, but only {len(sessions)} provided."
        )

    # Validate session IDs
    for sess in sessions:
        sess_id = sess["session_id"]
        if not validate_session_id(sess_id):
            logger.warning(f"Session ID '{sess_id}' does not match standard convention <YYYYMMDD>_<location>_<NN>")

    # Shuffle sessions reproducibly
    rng = np.random.RandomState(seed)
    sess_indices = np.arange(len(sessions))
    rng.shuffle(sess_indices)

    n_total = len(sessions)
    n_train = max(1, int(round(n_total * train_ratio)))
    n_val = max(1, int(round(n_total * val_ratio)))
    n_test = n_total - n_train - n_val

    # Adjust if test becomes 0
    if n_test <= 0 and n_total >= 3:
        n_train -= 1
        n_test = 1

    train_idx = sess_indices[:n_train]
    val_idx = sess_indices[n_train:n_train + n_val]
    test_idx = sess_indices[n_train + n_val:]

    splits_map = {
        "train": [sessions[i] for i in train_idx],
        "val": [sessions[i] for i in val_idx],
        "test": [sessions[i] for i in test_idx],
    }

    manifest_paths: Dict[str, Path] = {}

    for split_name, split_sessions in splits_map.items():
        manifest_file = out_dir / f"{split_name}_manifest.csv"
        rows = []
        for sess in split_sessions:
            rows.extend(sess.get("manifest_rows", []))

        fieldnames = ["session_id", "frame_path", "frame_index", "timestamp_ms"]
        with open(manifest_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        manifest_paths[split_name] = manifest_file
        logger.info(f"Split '{split_name}': {len(split_sessions)} sessions, {len(rows)} frames -> {manifest_file}")

    # Check for missing classes in val/test if label config provided
    if label_config_path and Path(label_config_path).exists():
        with open(label_config_path, "r") as f:
            label_data = yaml.safe_load(f)
        all_classes = set(str(v) for v in label_data.get("classes", {}).values())

        # Collect classes per split
        for split_name in ["val", "test"]:
            split_classes = set()
            for sess in splits_map[split_name]:
                for cls_name in sess.get("class_labels", []):
                    split_classes.add(cls_name)

            missing = all_classes - split_classes
            if missing:
                logger.warning(f"Class coverage warning for split '{split_name}': missing classes {missing}")

    # Run automated leakage assertion
    check_leakage(manifest_paths)

    return manifest_paths
