---
tags: [dataset/archived, dataset/intermediate]
---

# Resampled variants

Files (now in `_archive/`):
- `_archive/datasets/bp_dataset_resampledV2.csv`
- `_archive/datasets/bp_dataset_resampled_200_V2.csv`
- `_archive/models/bp_dataset_resampledV2.csv` (had been misplaced inside `models/`)
- `_archive/datasets/cleaned2_data.csv`, `cleaned_data (1).csv`, `cleaned_data_with_bmi.csv`, `df_with_nulls.csv`

## What

Iterative resampling and cleaning passes over the captured signals. Each represents a
different choice of target sample length (200 / 50 Hz) and / or imputation strategy.

## Why It's Archived

Superseded by [[all_features_dataset]], which is the canonical 200-sample feature matrix used
for the final training run.

## Linked

- [[all_features_dataset]]
- [[cleaned_data]]
- [[Methodology]]
