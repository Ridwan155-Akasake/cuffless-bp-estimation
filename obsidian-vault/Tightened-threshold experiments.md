---
tags: [model/experimental, model/archived]
---

# Tightened-threshold experiments

Files (now in `_archive/models/`):
- `multi_model_combined_tight_{rf,catboost,lgbm,adaboost,ridge}.pkl`
- `tight_model_combined_tight_systolic_BP_{rf,catboost,lgbm,adaboost,ridge}.pkl`
- `tight_model_combined_tight_diastolic_BP_{rf,catboost,lgbm,adaboost,ridge}.pkl`

## What

Run via `models/target_train_tightened.py`. Uses stricter feature filters / outlier
thresholds during training to see whether trimming noisy beats / outlier subjects improves
generalization.

## Trained On

- [[all_features_dataset]] with the "tight" filtering applied.

## Why They're Archived

The tightened variants did not consistently beat the un-tightened multi-output run on
held-out folds. The dataset is small enough that aggressive filtering removed useful signal
along with the noise.

## Superseded By

- [[random_forest_tuned_model]].

## Linked

- [[Methodology]]
- [[Multi-output combined experiments]]
