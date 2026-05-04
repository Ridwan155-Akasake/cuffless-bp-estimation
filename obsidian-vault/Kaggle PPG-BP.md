---
tags: [dataset/archived, dataset/external]
---

# Kaggle PPG-BP

Files (now in `_archive/datasets/`): `kaggel_features_df.csv`, `ir_local_features_df.csv`,
`red_local_features_df.csv`.

## What

External PPG-BP dataset from Kaggle, ingested via `models/process_kaggle_and_merge.py` and
feature-extracted into the local format used by this project.

## Why It's Archived

Tried as augmentation to compensate for the small in-house sample size, but the Kaggle
recordings used different sensor hardware and acquisition conditions; transferring its
features into this project's pipeline did not improve metrics. See [[Kaggle-track experiments]]
for the trained checkpoints.

## Linked

- [[Methodology]]
- [[Kaggle-track experiments]]
