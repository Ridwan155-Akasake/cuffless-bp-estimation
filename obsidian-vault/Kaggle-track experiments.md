---
tags: [model/experimental, model/archived]
---

# Kaggle-track experiments

Files (now in `_archive/models/`):
- `multi_model_kaggle_{rf,catboost,lgbm,adaboost,ridge}.pkl`
- `tight_model_kaggle_tight_systolic_BP_{rf,catboost,lgbm,adaboost,ridge}.pkl`
- `tight_model_kaggle_tight_diastolic_BP_{rf,catboost,lgbm,adaboost,ridge}.pkl`

## What

Same model families as the in-house track, but trained on Kaggle PPG-BP data merged in
through `models/process_kaggle_and_merge.py`.

## Trained On

- [[Kaggle PPG-BP]] (external dataset).

## Why They're Archived

The Kaggle data was captured with different sensor hardware and signal characteristics; the
resulting models did not transfer to this project's MAX30102 captures, and a joint train on
both sources reduced metrics versus training on the in-house data alone.

## Superseded By

- [[random_forest_tuned_model]] (in-house only).

## Linked

- [[Kaggle PPG-BP]]
- [[Methodology]]
