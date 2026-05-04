---
tags: [model/experimental, model/archived]
---

# Single-target RF baselines

Files (now in `_archive/models/`):
- `model_systolic_BP_rf.pkl` (~16 MB)
- `model_diastolic_BP_rf.pkl` (~16 MB)
- `random_forest_best_mae_model2.pkl`

## What

The earliest approach: train **two separate** Random Forest regressors — one per BP target.
These were the baseline before switching to a single multi-output model.

## Trained On

- An earlier version of [[all_features_dataset]] (full 400-column input, before top-K mutual-information feature selection).

## Why It's Archived

- Doubles model size for no gain.
- Multi-output RF — [[random_forest_tuned_model]] — beats it on every metric and is a single artifact to deploy.

## Superseded By

[[random_forest_tuned_model]].

## Linked

- [[Methodology]]
- [[Results]]
