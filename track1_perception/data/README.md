# Data Directory

This directory stores raw dataset recordings, extracted frame sequences, and split manifests for Track 1 Perception.

> **Note**: Actual dataset recordings and image files in this directory are gitignored to prevent committing large binary files to the repository.

## Subdirectories

- `raw/`: Raw session recordings structured as `raw/<session_id>/{raw_video.mp4, frames/, annotations/}`
- `splits/`: Split manifests (`train_manifest.csv`, `val_manifest.csv`, `test_manifest.csv`)

## Session ID Standard
Format: `<YYYYMMDD>_<location>_<NN>` (e.g. `20261012_corridorA_01`). See `docs/data_conventions.md` for full details.
