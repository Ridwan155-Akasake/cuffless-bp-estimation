---
tags: [dataset/archived, dataset/ablation]
---

# Feature ablation experiments

Files (now in `_archive/datasets/`):
- `ir_features_dataset.csv`, `red_features_dataset.csv` — single-channel only.
- `ir_red_demographics_dataset.csv` — IR + RED + demographics, no vitals.
- `ir_red_vitals_dataset.csv` — IR + RED + HR/SpO₂, no demographics.
- `ppg_only_dataset.csv` — PPG signals + demographics, no extracted features.
- `features_no_demographics_df.csv`, `features_no_vitals_df.csv`.
- `ir_features_no_demographics.csv`, `ir_features_no_vitals.csv`,
  `red_features_no_demographics.csv`, `red_features_no_vitals.csv`,
  `red_features_only.csv`, `ir_features_with_demographics_vitals.csv`,
  `red_features_with_demographics_vitals.csv`, `ir_ppg_only.csv`,
  `extract_features_only_df.csv`, `extracted_features.csv`,
  `combined_features_labels.csv`, `total_features_dataset.csv`,
  `ppg_features_dataset.csv`, `features.csv`, `featuresV2.csv`,
  `labels.csv`, `labelsV2.csv`.

## What

Each file reflects an ablation: hold one feature group out (channel, demographics, vitals) and
see how the model degrades.

## Headline Finding

> Adding RED-channel features alongside IR was **redundant** and slightly **degraded** the
> regression. The deployed model — [[random_forest_tuned_model]] — therefore uses
> **IR-only features + demographics**.

## Why It's Archived

Each variant served a single ablation question; the final pipeline only needs
[[all_features_dataset]] and the selected feature-subset logic in
`models/train_bp_models.py`.

## Linked

- [[Methodology]]
- [[Results]]
